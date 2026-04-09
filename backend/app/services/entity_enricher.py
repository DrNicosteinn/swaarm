"""Entity Enricher — web-enriches extracted entities via Serper + page fetching + LLM extraction.

Pipeline per entity:
  1. Serper Google search → 10 results (title, snippet, URL)
  2. Fetch top 3 pages in parallel (httpx, 5s timeout, max 10K chars/page)
  3. LLM extraction call → structured EnrichmentResult

Usage:
    enricher = EntityEnricher(llm, usage_tracker)
    results = await enricher.enrich_batch(entities, scenario_context, on_progress=callback)
"""

import asyncio
import re
from typing import Any

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from app.core.config import settings
from app.llm.base import LLMProvider, LLMUsageTracker
from app.services.smart_decision import ExtractedEntity

# ── Models ───────────────────────────────────────────────────────────


class EnrichmentResult(BaseModel):
    """Structured data extracted from web enrichment for a single entity."""

    entity_name: str
    success: bool = True

    # Verified identity
    verified_name: str = ""
    verified_title: str = ""
    verified_company: str = ""
    industry: str = ""
    location: str = ""

    # Behavioral profile
    communication_style: str = ""  # formal, casual, provokativ, etc.
    known_positions: list[str] = Field(default_factory=list)  # public stances on relevant topics
    influence_level: str = "medium"  # high, medium, low

    # Context
    recent_context: str = ""  # "Recently in the news because..."
    bio_summary: str = ""  # 2-3 sentence bio

    # Sources
    sources: list[str] = Field(default_factory=list)  # URLs used


# ── Constants ────────────────────────────────────────────────────────

_SERPER_URL = "https://google.serper.dev/search"

_MAX_PAGE_CHARS = 10_000
_FETCH_TIMEOUT = 5.0
_MAX_FETCH_ATTEMPTS = 5  # Try up to 5 URLs to get 3 successful fetches
_TARGET_PAGES = 3

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

_EXTRACTION_PROMPT = """\
Du bist ein Recherche-Assistent. Extrahiere verifizierte Informationen ueber die folgende Entity \
aus den bereitgestellten Suchergebnissen und Webseiten-Texten.

## Entity
Name: {entity_name}
Typ: {entity_type}
Rolle im Szenario: {role_in_scenario}

## Szenario-Kontext
{scenario_context}

## Suchergebnisse (Snippets)
{snippets}

## Webseiten-Texte
{page_texts}

## Anweisungen
- Extrahiere NUR verifizierte Fakten aus den Quellen
- Keine Spekulation oder Erfindung
- Kommunikationsstil: Wie kommuniziert diese Person/Organisation oeffentlich?
- Bekannte Positionen: Relevante oeffentliche Standpunkte zum Szenario-Thema
- Aktueller Kontext: Was ist kuerzlich passiert, das relevant ist?

## Antwort-Format (NUR JSON, kein anderer Text)
{{
  "verified_name": "Offizieller Name",
  "verified_title": "Aktuelle Position/Titel",
  "verified_company": "Organisation (falls Person)",
  "industry": "Branche",
  "location": "Standort",
  "communication_style": "formal|casual|provokativ|sachlich|diplomatisch",
  "known_positions": ["Position 1 zum Thema", "Position 2"],
  "influence_level": "high|medium|low",
  "recent_context": "Kuerzlich in den Nachrichten wegen...",
  "bio_summary": "2-3 Saetze Zusammenfassung"
}}"""


# ── HTML to Text ─────────────────────────────────────────────────────


def _html_to_text(html: str) -> str:
    """Simple HTML tag stripping. No external dependency needed."""
    # Remove script and style blocks
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode common entities
    for entity, char in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&nbsp;", " "), ("&quot;", '"')]:
        text = text.replace(entity, char)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text[:_MAX_PAGE_CHARS]


# ── Service ──────────────────────────────────────────────────────────


class EntityEnricher:
    """Enriches entities via Serper web search + page fetching + LLM extraction."""

    def __init__(self, llm: LLMProvider, usage_tracker: LLMUsageTracker | None = None):
        self.llm = llm
        self.usage = usage_tracker or LLMUsageTracker()

    async def enrich_batch(
        self,
        entities: list[ExtractedEntity],
        scenario_context: str,
        on_progress: Any | None = None,
        max_concurrent: int = 3,
    ) -> list[EnrichmentResult]:
        """Enrich all entities in parallel (max_concurrent at a time).

        Args:
            entities: Entities to enrich (only those with enrichment=ENRICH).
            scenario_context: Original user input for context.
            on_progress: Async callback(EnrichmentResult) called per completed entity.
            max_concurrent: Max parallel enrichment operations.

        Returns:
            List of EnrichmentResult (one per entity, including failures).
        """
        if not settings.serper_api_key:
            logger.warning("No SERPER_API_KEY configured — skipping all enrichment")
            return [EnrichmentResult(entity_name=e.name, success=False) for e in entities]

        semaphore = asyncio.Semaphore(max_concurrent)
        results: list[EnrichmentResult] = []

        async def _enrich_one(entity: ExtractedEntity) -> EnrichmentResult:
            async with semaphore:
                result = await self.enrich_entity(entity, scenario_context)
                if on_progress:
                    await on_progress(result)
                return result

        tasks = [_enrich_one(e) for e in entities]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return list(results)

    async def enrich_entity(self, entity: ExtractedEntity, scenario_context: str) -> EnrichmentResult:
        """Full enrichment pipeline for a single entity.

        1. Serper search
        2. Fetch top 3 pages
        3. LLM extraction
        """
        try:
            # Step 1: Serper search
            search_results = await self._serper_search(entity)
            if not search_results:
                logger.warning(f"No search results for entity: {entity.name}")
                return EnrichmentResult(entity_name=entity.name, success=False)

            # Step 2: Fetch top pages
            snippets = "\n".join(f"- {r['title']}: {r['snippet']}" for r in search_results[:10])
            urls = [r["link"] for r in search_results if r.get("link")]
            page_texts = await self._fetch_pages(urls)

            # Step 3: LLM extraction
            result = await self._extract_with_llm(entity, scenario_context, snippets, page_texts)
            result.sources = urls[:_TARGET_PAGES]
            return result

        except Exception as e:
            logger.error(f"Enrichment failed for {entity.name}: {e}")
            return EnrichmentResult(entity_name=entity.name, success=False)

    async def _serper_search(self, entity: ExtractedEntity) -> list[dict]:
        """Search Google via Serper API."""
        query = f"{entity.name} {entity.role_in_scenario}"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                _SERPER_URL,
                json={"q": query, "gl": "ch", "hl": "de", "num": 10},
                headers={
                    "X-API-KEY": settings.serper_api_key,
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        results = data.get("organic", [])
        logger.debug(f"Serper returned {len(results)} results for '{query}'")
        return results

    async def _fetch_pages(self, urls: list[str]) -> str:
        """Fetch top pages in parallel, return concatenated text."""
        if not urls:
            return ""

        fetched: list[str] = []

        async with httpx.AsyncClient(
            timeout=_FETCH_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        ) as client:
            for url in urls[:_MAX_FETCH_ATTEMPTS]:
                if len(fetched) >= _TARGET_PAGES:
                    break
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("text/"):
                        text = _html_to_text(resp.text)
                        if len(text) > 100:  # Skip near-empty pages
                            fetched.append(f"### Quelle: {url}\n{text}")
                            logger.debug(f"Fetched {len(text)} chars from {url}")
                except (httpx.HTTPError, httpx.TimeoutException) as e:
                    logger.debug(f"Failed to fetch {url}: {e}")
                    continue

        if not fetched:
            return "(Keine Webseiten konnten geladen werden)"

        return "\n\n".join(fetched)

    async def _extract_with_llm(
        self,
        entity: ExtractedEntity,
        scenario_context: str,
        snippets: str,
        page_texts: str,
    ) -> EnrichmentResult:
        """Use LLM to extract structured data from search results + page texts."""
        prompt = _EXTRACTION_PROMPT.format(
            entity_name=entity.name,
            entity_type=entity.entity_type.value,
            role_in_scenario=entity.role_in_scenario,
            scenario_context=scenario_context[:2000],
            snippets=snippets[:3000],
            page_texts=page_texts[:30000],
        )

        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1000,
        )
        self.usage.record(response)

        # Parse JSON response
        content = response.content or "{}"
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            return EnrichmentResult(entity_name=entity.name, success=False)

        import json

        data = json.loads(content[start:end])

        return EnrichmentResult(
            entity_name=entity.name,
            success=True,
            verified_name=data.get("verified_name", ""),
            verified_title=data.get("verified_title", ""),
            verified_company=data.get("verified_company", ""),
            industry=data.get("industry", ""),
            location=data.get("location", ""),
            communication_style=data.get("communication_style", ""),
            known_positions=data.get("known_positions", []),
            influence_level=data.get("influence_level", "medium"),
            recent_context=data.get("recent_context", ""),
            bio_summary=data.get("bio_summary", ""),
        )
