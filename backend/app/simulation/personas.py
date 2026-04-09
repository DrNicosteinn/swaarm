"""Persona generator — creates diverse, DACH-calibrated personas for simulation.

Pipeline:
1. Determine stakeholder mix from scenario
2. Generate ~500 base personas via LLM (batches of 10)
3. Scale to target count via parametric variation
"""

import json
import random
import uuid
from collections.abc import Callable
from copy import deepcopy
from typing import Any

from loguru import logger
from pydantic import BaseModel

from app.llm.base import LLMProvider, LLMUsageTracker
from app.models.persona import AgentTier, BigFive, OpinionSeeds, Persona, PersonaSource, PostingStyle
from app.models.simulation import ScenarioControversity, TierDistribution
from app.services.entity_enricher import EnrichmentResult
from app.services.smart_decision import EntityType, ExtractedEntity, SimulationDecision

# DACH demographic distributions for calibration
DACH_AGE_DISTRIBUTION = [
    (18, 24, 0.15),  # 15% — oversampled for social media
    (25, 34, 0.24),
    (35, 44, 0.22),
    (45, 54, 0.18),
    (55, 64, 0.13),
    (65, 85, 0.08),
]

DACH_COUNTRY_DISTRIBUTION = [
    ("DE", 0.76),
    ("CH", 0.16),
    ("AT", 0.08),
]

DACH_REGIONS = {
    "DE": ["Berlin", "München", "Hamburg", "Frankfurt", "Köln", "Stuttgart", "Düsseldorf", "Leipzig"],
    "CH": ["Zürich", "Bern", "Basel", "Genf", "Lausanne", "Luzern", "St. Gallen", "Winterthur"],
    "AT": ["Wien", "Graz", "Linz", "Salzburg", "Innsbruck", "Klagenfurt"],
}

SINUS_MILIEUS = [
    ("Konservativ-Gehobenes", 0.11),
    ("Postmaterielles", 0.12),
    ("Performer", 0.10),
    ("Expeditives", 0.10),
    ("Neo-Ökologisches", 0.08),
    ("Adaptiv-Pragmatische Mitte", 0.12),
    ("Konsum-Hedonistisches", 0.08),
    ("Prekäres", 0.09),
    ("Nostalgisch-Bürgerliches", 0.11),
    ("Traditionelles", 0.09),
]

# Stakeholder templates per scenario type
STAKEHOLDER_TEMPLATES = {
    "corporate_crisis": {
        "employees": 0.15,
        "customers": 0.25,
        "media": 0.05,
        "competitors": 0.03,
        "regulators": 0.02,
        "investors": 0.05,
        "general_public": 0.35,
        "activists": 0.05,
        "politicians": 0.05,
    },
    "product_launch": {
        "target_customers": 0.35,
        "existing_customers": 0.20,
        "media": 0.05,
        "influencers": 0.10,
        "competitors": 0.05,
        "general_public": 0.20,
        "analysts": 0.05,
    },
    "employer_branding": {
        "employees": 0.25,
        "job_seekers": 0.20,
        "hr_professionals": 0.10,
        "competitors_employees": 0.10,
        "media": 0.05,
        "general_public": 0.20,
        "recruiters": 0.10,
    },
    "default": {
        "supporters": 0.25,
        "critics": 0.20,
        "neutral_observers": 0.30,
        "media": 0.05,
        "influencers": 0.05,
        "general_public": 0.15,
    },
}

TONES = ["sachlich", "emotional", "provokativ", "humorvoll", "analytisch", "umgangssprachlich"]
FREQUENCIES = ["daily", "weekly", "monthly", "rarely"]

# ── Step 1: Research the company/scenario to find real stakeholders ──
RESEARCH_PROMPT = """Analysiere dieses Szenario und erstelle eine Liste von {count} konkreten Personen-Rollen,
die in der oeffentlichen Debatte dazu relevant waeren.

Szenario: {scenario}
Unternehmen: {company}
Branche: {industry}

Erstelle eine JSON-Liste mit {count} Eintraegen. Jeder Eintrag beschreibt EINE konkrete Person:
[{{"role":"Stakeholder-Rolle (z.B. employees, customers, media, regulators, investors, general_public, activists, politicians)",
"name":"Realistischer DACH-Name",
"occupation":"Konkreter Beruf/Position (z.B. 'CEO von {company}', 'Kundenberater', 'NZZ-Wirtschaftsredakteurin')",
"age":30,
"gender":"male/female",
"connection_to":"ID der Person zu der diese verbunden ist (z.B. 'p0' fuer das Unternehmen), oder null",
"connection_label":"Art der Beziehung (z.B. 'arbeitet bei', 'Kunde von', 'berichtet ueber', 'Ehefrau von')",
"sentiment_bias":-0.3}}]

REGELN:
- Person p0 MUSS das Unternehmen/die Organisation selbst sein (role: "company")
- Personen p1-p5: Fuehrungskraeftee und Schluesssel-Mitarbeiter, verbunden mit p0
- Personen p6+: Kunden, Journalisten, Familienangehoerige, Politiker, Experten etc.
- Jede Person hat EINE connection_to (zu wem sie verbunden ist) — NICHT zu vielen!
- Familienangehoerige verbinden sich mit dem Mitarbeiter, NICHT mit der Firma
- sentiment_bias: -1 (sehr negativ) bis +1 (sehr positiv) gegenueber dem Szenario
- Realistische DACH-Namen (deutsch/schweizerdeutsch/oesterreichisch)
- Berufe muessen zum Szenario und Unternehmen passen

Antworte NUR mit dem JSON-Array, kein anderer Text."""

# ── Step 2: Generate full persona data for each role ──
SINGLE_PERSONA_PROMPT = """Erstelle eine detaillierte Persona fuer eine Social-Media-Simulation:

Name: {name}
Rolle: {role}
Beruf: {occupation}
Alter: {age}
Geschlecht: {gender}
Szenario: {scenario}

Antworte NUR mit einem JSON-Objekt:
{{"country":"DE/CH/AT","region":"Stadt",
"education":"Bildung",
"big_five":{{"openness":0-1,"conscientiousness":0-1,"extraversion":0-1,"agreeableness":0-1,"neuroticism":0-1}},
"posting_style":{{"tone":"sachlich/emotional/provokativ/humorvoll","frequency":"daily/weekly/monthly/rarely","typical_topics":["2-3 Themen"]}},
"opinions":{{"trust_institutions":0-1,"environmental_concern":0-1,"tech_optimism":0-1,"economic_anxiety":0-1,"social_progressivism":0-1}},
"interests":["3-5 Interessen"],
"bio":"1-2 Saetze ueber diese Person und ihre Haltung zum Szenario"}}

Big Five: echte Variation, NICHT alle 0.5!"""

REAL_PERSONA_PROMPT = """Erstelle eine detaillierte Persona basierend auf recherchierten Daten einer realen Person/Organisation.

## Recherchierte Daten
Name: {verified_name}
Titel: {verified_title}
Organisation: {verified_company}
Branche: {industry}
Standort: {location}
Kommunikationsstil: {communication_style}
Bekannte Positionen: {known_positions}
Einfluss-Level: {influence_level}
Aktueller Kontext: {recent_context}
Bio: {bio_summary}

## Szenario-Kontext
{scenario}

## Anweisungen
Erstelle eine realistische Persona die das Verhalten dieser Person/Organisation auf Social Media simuliert.
Die Persona soll sich konsistent mit den bekannten oeffentlichen Positionen verhalten.

Antworte NUR mit einem JSON-Objekt:
{{"country":"DE/CH/AT","region":"Stadt",
"education":"Bildung",
"big_five":{{"openness":0-1,"conscientiousness":0-1,"extraversion":0-1,"agreeableness":0-1,"neuroticism":0-1}},
"posting_style":{{"tone":"sachlich/emotional/provokativ/humorvoll","frequency":"daily/weekly/monthly/rarely","typical_topics":["2-3 Themen"]}},
"opinions":{{"trust_institutions":0-1,"environmental_concern":0-1,"tech_optimism":0-1,"economic_anxiety":0-1,"social_progressivism":0-1}},
"interests":["3-5 Interessen"],
"bio":"1-2 Saetze ueber diese Person und ihre Haltung zum Szenario"}}"""


class PersonaGenerationConfig(BaseModel):
    """Configuration for persona generation."""

    scenario_text: str
    scenario_type: str = "default"
    target_count: int = 200
    base_persona_count: int = 500
    controversity: ScenarioControversity = ScenarioControversity.STANDARD
    seed: int | None = None
    batch_size: int = 25
    # Extracted from scenario for better persona generation
    company: str = ""
    industry: str = ""


class PersonaGenerator:
    """Generates diverse, DACH-calibrated personas for simulation."""

    def __init__(self, llm: LLMProvider, usage_tracker: LLMUsageTracker | None = None):
        self.llm = llm
        self.usage = usage_tracker or LLMUsageTracker()

    async def generate(
        self,
        config: PersonaGenerationConfig,
        on_progress: Callable[[int], None] | None = None,
        on_batch: Callable[[list["Persona"]], Any] | None = None,
        decision: SimulationDecision | None = None,
        enrichment_results: list[EnrichmentResult] | None = None,
    ) -> list[Persona]:
        """Generate personas for a simulation.

        If decision + enrichment_results are provided (entity-pipeline flow):
          1. Create real personas from enrichment data (fast, appears first in graph)
          2. Generate remaining personas via LLM research + batch flow
          3. Set persona_source on all personas

        Otherwise (legacy flow):
          1. Research stakeholders via LLM
          2. Generate personas in parallel
          3. Assign tiers + flags + scale

        Args:
            on_progress: Called with number of personas generated so far after each batch.
            on_batch: Async callback with list of newly generated personas after each batch.
            decision: SimulationDecision from SmartDecisionEngine (entity-pipeline flow).
            enrichment_results: Web enrichment results for entities.
        """
        rng = random.Random(config.seed)

        import asyncio

        all_personas: list[Persona] = []
        _counter = 0
        _lock = asyncio.Lock()

        # ── Entity-Pipeline Flow ──
        if decision is not None:
            enrichment_map = {}
            if enrichment_results:
                enrichment_map = {r.entity_name: r for r in enrichment_results if r.success}

            # Phase A: Create real personas from enriched entities
            real_entities = [
                e
                for e in decision.entities
                if e.entity_type in (EntityType.REAL_PERSON, EntityType.REAL_COMPANY) and e.persona_count > 0
            ]

            if real_entities:
                logger.info(f"Creating real personas for {len(real_entities)} entities")
                real_personas = await self._create_real_personas(
                    real_entities, enrichment_map, config.scenario_text
                )
                all_personas.extend(real_personas)
                _counter = len(real_personas)

                if on_progress:
                    on_progress(_counter)
                if on_batch:
                    res = on_batch(real_personas)
                    if asyncio.iscoroutine(res):
                        await res

                logger.info(f"Created {len(real_personas)} real personas from enrichment data")

            # Phase B: Generate remaining personas via research + LLM
            remaining_count = config.target_count - len(all_personas)
            if remaining_count > 0:
                # Build context about existing real personas for the research prompt
                existing_context = ""
                if all_personas:
                    names = ", ".join(p.name for p in all_personas[:20])
                    existing_context = f"\nBereits erstellte reale Personas: {names}. Generiere ergaenzende Personas die zu diesem Mix passen."

                roster = await self._research_stakeholders(
                    config.scenario_text + existing_context,
                    config.company,
                    config.industry,
                    remaining_count,
                )
                logger.info(f"Research complete: {len(roster)} additional persona roles")

                semaphore = asyncio.Semaphore(4)

                async def _gen_one(entry: dict, idx: int) -> None:
                    nonlocal _counter
                    async with semaphore:
                        persona = await self._generate_single_persona(entry, config.scenario_text, idx)
                        # Determine persona source from decision
                        role_entities = [
                            e
                            for e in decision.entities
                            if e.entity_type == EntityType.ROLE and e.persona_count > 0
                        ]
                        if entry.get("role") in [e.name for e in role_entities]:
                            persona.persona_source = PersonaSource.ROLE_BASED
                        else:
                            persona.persona_source = PersonaSource.GENERATED

                    async with _lock:
                        all_personas.append(persona)
                        _counter += 1
                        if on_progress:
                            on_progress(_counter)
                        if on_batch:
                            res = on_batch([persona])
                            if asyncio.iscoroutine(res):
                                await res

                tasks = [_gen_one(entry, i) for i, entry in enumerate(roster)]
                await asyncio.gather(*tasks, return_exceptions=True)

        # ── Legacy Flow (no decision) ──
        else:
            stakeholder_mix = self._get_stakeholder_mix(config.scenario_type, config.base_persona_count)
            logger.info(f"Stakeholder mix: {stakeholder_mix}")

            roster = await self._research_stakeholders(
                config.scenario_text, config.company, config.industry, config.target_count
            )
            logger.info(f"Research complete: {len(roster)} persona roles identified")

            semaphore = asyncio.Semaphore(4)

            async def _gen_one_legacy(entry: dict, idx: int) -> None:
                nonlocal _counter
                async with semaphore:
                    persona = await self._generate_single_persona(entry, config.scenario_text, idx)

                async with _lock:
                    all_personas.append(persona)
                    _counter += 1
                    if on_progress:
                        on_progress(_counter)
                    if on_batch:
                        res = on_batch([persona])
                        if asyncio.iscoroutine(res):
                            await res

            tasks = [_gen_one_legacy(entry, i) for i, entry in enumerate(roster)]
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"Generated {len(all_personas)} personas via LLM (parallel, streamed)")

        # Scale to target count if needed (before tier assignment)
        if config.target_count > len(all_personas):
            personas = self._scale_personas(all_personas, config.target_count, rng)
        else:
            personas = all_personas[: config.target_count]

        # Assign tiers (globally, after scaling to final count)
        tier_dist = TierDistribution.for_controversity(config.controversity)
        self._assign_tiers(personas, tier_dist, rng)

        # Assign zealot/contrarian flags
        self._assign_special_flags(personas, rng)

        logger.info(
            f"Persona generation complete: {len(personas)} personas, "
            f"LLM cost: ${self.usage.total_cost_usd:.4f}"
        )

        return personas

    async def _create_real_personas(
        self,
        entities: list[ExtractedEntity],
        enrichment_map: dict[str, EnrichmentResult],
        scenario_context: str,
    ) -> list[Persona]:
        """Create personas directly from enriched entity data.

        For real_person: 1 persona with enriched data.
        For real_company: multiple associated personas (CEO, spokesperson, employee).
        """
        import asyncio

        personas: list[Persona] = []
        semaphore = asyncio.Semaphore(4)

        async def _create_one(entity: ExtractedEntity) -> list[Persona]:
            async with semaphore:
                enrichment = enrichment_map.get(entity.name)
                if enrichment and enrichment.success:
                    source = PersonaSource.REAL_ENRICHED
                    sources = ["web_search"]
                else:
                    source = PersonaSource.REAL_MINIMAL
                    sources = ["document"]
                    enrichment = EnrichmentResult(entity_name=entity.name, success=False)

                if entity.entity_type == EntityType.REAL_PERSON:
                    persona = await self._create_real_person_persona(
                        entity, enrichment, scenario_context, source, sources
                    )
                    return [persona]
                elif entity.entity_type == EntityType.REAL_COMPANY:
                    company_personas = await self._create_company_personas(
                        entity, enrichment, scenario_context, source, sources
                    )
                    return company_personas
                return []

        tasks = [_create_one(e) for e in entities]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, list):
                personas.extend(result)
        return personas

    async def _create_real_person_persona(
        self,
        entity: ExtractedEntity,
        enrichment: EnrichmentResult,
        scenario_context: str,
        source: PersonaSource,
        sources: list[str],
    ) -> Persona:
        """Create a single persona from a real person entity + enrichment data."""
        prompt = REAL_PERSONA_PROMPT.format(
            verified_name=enrichment.verified_name or entity.name,
            verified_title=enrichment.verified_title or entity.sub_type,
            verified_company=enrichment.verified_company or "",
            industry=enrichment.industry or "",
            location=enrichment.location or "",
            communication_style=enrichment.communication_style or "sachlich",
            known_positions=", ".join(enrichment.known_positions)
            if enrichment.known_positions
            else "unbekannt",
            influence_level=enrichment.influence_level,
            recent_context=enrichment.recent_context or "",
            bio_summary=enrichment.bio_summary or entity.role_in_scenario,
            scenario=scenario_context[:1000],
        )

        persona_data = {}
        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=500,
            )
            if self.usage:
                self.usage.record(response)
            content = response.content or ""
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                persona_data = json.loads(content[start:end])
        except Exception as e:
            logger.warning(f"Real persona generation failed for {entity.name}: {e}")

        big_five_raw = persona_data.get("big_five", {})
        style_raw = persona_data.get("posting_style", {})
        opinions_raw = persona_data.get("opinions", {})

        return Persona(
            id=f"agent-{uuid.uuid4().hex[:8]}",
            name=enrichment.verified_name or entity.name,
            age=45,  # Default for public figures
            gender="male",
            country=persona_data.get("country", "DE"),
            region=persona_data.get("region", enrichment.location or "Zürich"),
            occupation=enrichment.verified_title or entity.sub_type or entity.role_in_scenario,
            industry=enrichment.industry or "",
            education=persona_data.get("education", ""),
            big_five=BigFive(
                openness=self._clamp(big_five_raw.get("openness", 0.6)),
                conscientiousness=self._clamp(big_five_raw.get("conscientiousness", 0.7)),
                extraversion=self._clamp(big_five_raw.get("extraversion", 0.6)),
                agreeableness=self._clamp(big_five_raw.get("agreeableness", 0.5)),
                neuroticism=self._clamp(big_five_raw.get("neuroticism", 0.3)),
            ),
            posting_style=PostingStyle(
                tone=style_raw.get("tone", enrichment.communication_style or "sachlich"),
                frequency=style_raw.get("frequency", "weekly"),
                typical_topics=style_raw.get("typical_topics", []),
            ),
            opinions=OpinionSeeds(
                trust_institutions=self._clamp(opinions_raw.get("trust_institutions", 0.5)),
                environmental_concern=self._clamp(opinions_raw.get("environmental_concern", 0.5)),
                tech_optimism=self._clamp(opinions_raw.get("tech_optimism", 0.5)),
                economic_anxiety=self._clamp(opinions_raw.get("economic_anxiety", 0.5)),
                social_progressivism=self._clamp(opinions_raw.get("social_progressivism", 0.5)),
            ),
            interests=persona_data.get("interests", []),
            stakeholder_role=entity.role_in_scenario,
            bio=persona_data.get("bio", enrichment.bio_summary or f"{entity.name}, {entity.sub_type}"),
            persona_source=source,
            source_entity_name=entity.name,
            enrichment_sources=sources,
        )

    async def _create_company_personas(
        self,
        entity: ExtractedEntity,
        enrichment: EnrichmentResult,
        scenario_context: str,
        source: PersonaSource,
        sources: list[str],
    ) -> list[Persona]:
        """Create multiple personas for a company entity (CEO, spokesperson, employee)."""
        count = min(entity.persona_count, 5)
        # For the first persona, use enrichment data directly (like the company account)
        company_persona = await self._create_real_person_persona(
            entity, enrichment, scenario_context, source, sources
        )
        company_persona.occupation = f"Offizieller Account von {entity.name}"
        personas = [company_persona]

        # Generate additional associated personas via research
        if count > 1:
            for i in range(1, count):
                role_names = [
                    "Unternehmenssprecher/in",
                    "Mitarbeiter/in",
                    "Fuehrungskraft",
                    "Pressesprecher/in",
                ]
                role = role_names[i % len(role_names)]
                entry = {
                    "name": f"{role} bei {entity.name}",
                    "role": "employees",
                    "occupation": f"{role} bei {entity.name}",
                    "age": random.randint(30, 55),
                    "gender": random.choice(["male", "female"]),
                }
                persona = await self._generate_single_persona(entry, scenario_context, i)
                persona.persona_source = source
                persona.source_entity_name = entity.name
                persona.enrichment_sources = sources
                personas.append(persona)

        return personas

    async def _generate_batch(
        self,
        role: str,
        scenario: str,
        batch_size: int,
        previous_names: list[str],
    ) -> list[Persona]:
        """Generate a batch of personas via LLM."""
        previous_hint = ""
        if previous_names:
            names_str = ", ".join(previous_names)
            previous_hint = f"Bereits generierte Personas (erzeuge ANDERE): {names_str}"

        prompt = BATCH_GENERATION_PROMPT.format(
            batch_size=batch_size,
            role=role,
            scenario=scenario,
            previous_hint=previous_hint,
        )

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0,  # High temperature for diversity
                max_tokens=batch_size * 400,
            )
            self.usage.record(response)

            # Parse JSON response
            content = response.content or ""
            # Try to extract JSON array from response
            personas = self._parse_persona_json(content, role)
            return personas

        except Exception as e:
            logger.warning(f"Batch generation failed for role '{role}': {e}")
            # Fallback: generate simple personas without LLM
            return self._generate_fallback_batch(role, batch_size)

    def _parse_persona_json(self, content: str, role: str) -> list[Persona]:
        """Parse LLM response into Persona objects."""
        # Try to find JSON array in response
        start = content.find("[")
        end = content.rfind("]") + 1
        if start == -1 or end == 0:
            logger.warning("No JSON array found in LLM response")
            return []

        try:
            raw_personas = json.loads(content[start:end])
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            return []

        personas = []
        for raw in raw_personas:
            try:
                persona = self._raw_to_persona(raw, role)
                personas.append(persona)
            except Exception as e:
                logger.warning(f"Failed to parse persona: {e}")
                continue

        return personas

    def _raw_to_persona(self, raw: dict, role: str) -> Persona:
        """Convert raw LLM JSON to a Persona object."""
        big_five_raw = raw.get("big_five", {})
        opinions_raw = raw.get("opinions", {})
        style_raw = raw.get("posting_style", {})

        return Persona(
            id=f"agent-{uuid.uuid4().hex[:8]}",
            name=raw.get("name", "Unbekannt"),
            age=max(18, min(85, int(raw.get("age", 30)))),
            gender=raw.get("gender", "female"),
            country=raw.get("country", "DE"),
            region=raw.get("region", "Berlin"),
            occupation=raw.get("occupation", "Angestellte/r"),
            industry=raw.get("industry", ""),
            education=raw.get("education", ""),
            sinus_milieu=raw.get("sinus_milieu", ""),
            big_five=BigFive(
                openness=self._clamp(big_five_raw.get("openness", 0.5)),
                conscientiousness=self._clamp(big_five_raw.get("conscientiousness", 0.5)),
                extraversion=self._clamp(big_five_raw.get("extraversion", 0.5)),
                agreeableness=self._clamp(big_five_raw.get("agreeableness", 0.5)),
                neuroticism=self._clamp(big_five_raw.get("neuroticism", 0.5)),
            ),
            posting_style=PostingStyle(
                tone=style_raw.get("tone", "sachlich"),
                frequency=style_raw.get("frequency", "weekly"),
                typical_topics=style_raw.get("typical_topics", []),
            ),
            opinions=OpinionSeeds(
                trust_institutions=self._clamp(opinions_raw.get("trust_institutions", 0.5)),
                environmental_concern=self._clamp(opinions_raw.get("environmental_concern", 0.5)),
                tech_optimism=self._clamp(opinions_raw.get("tech_optimism", 0.5)),
                economic_anxiety=self._clamp(opinions_raw.get("economic_anxiety", 0.5)),
                social_progressivism=self._clamp(opinions_raw.get("social_progressivism", 0.5)),
            ),
            interests=raw.get("interests", []),
            stakeholder_role=role,
            bio=raw.get("bio", ""),
        )

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
        """Clamp a value to [low, high]."""
        try:
            return max(low, min(high, float(value)))
        except (TypeError, ValueError):
            return 0.5

    async def _research_stakeholders(
        self, scenario: str, company: str, industry: str, count: int
    ) -> list[dict]:
        """Phase A: One LLM call to research and plan all persona roles."""
        prompt = RESEARCH_PROMPT.format(
            scenario=scenario,
            company=company or "das Unternehmen",
            industry=industry or "unbekannt",
            count=count,
        )

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=count * 150,
            )
            if self.usage:
                self.usage.record(response)

            content = response.content or ""
            # Extract JSON array
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > start:
                roster = json.loads(content[start:end])
                # Ensure we have the right count
                return roster[:count]
        except Exception as e:
            logger.warning(f"Research call failed: {e}")

        # Fallback: generate simple role list
        return self._fallback_roster(scenario, count)

    def _fallback_roster(self, scenario: str, count: int) -> list[dict]:
        """Generate a basic roster without LLM (fallback)."""
        roster = [
            {
                "role": "company",
                "name": "Unternehmen",
                "occupation": "Organisation",
                "age": 0,
                "gender": "male",
                "connection_to": None,
                "connection_label": None,
                "sentiment_bias": 0.0,
            }
        ]
        roles = ["employees", "customers", "media", "general_public", "investors", "politicians"]
        for i in range(1, count):
            role = roles[i % len(roles)]
            roster.append(
                {
                    "role": role,
                    "name": f"Person {i}",
                    "occupation": role,
                    "age": random.randint(25, 60),
                    "gender": random.choice(["male", "female"]),
                    "connection_to": "p0",
                    "connection_label": "verbunden mit",
                    "sentiment_bias": random.uniform(-0.5, 0.3),
                }
            )
        return roster

    async def _generate_single_persona(self, entry: dict, scenario: str, index: int) -> Persona:
        """Phase B: Generate one full persona from a roster entry via LLM."""
        name = entry.get("name", f"Person {index}")
        role = entry.get("role", "general_public")
        occupation = entry.get("occupation", "Angestellte/r")
        age = entry.get("age", 35)
        gender = entry.get("gender", "female")

        prompt = SINGLE_PERSONA_PROMPT.format(
            name=name,
            role=role,
            occupation=occupation,
            age=age,
            gender=gender,
            scenario=scenario,
        )

        persona_data = {}
        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=400,
            )
            if self.usage:
                self.usage.record(response)

            content = response.content or ""
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                persona_data = json.loads(content[start:end])
        except Exception as e:
            logger.warning(f"Single persona generation failed for {name}: {e}")

        # Build persona from research entry + LLM enrichment
        big_five_raw = persona_data.get("big_five", {})
        style_raw = persona_data.get("posting_style", {})
        opinions_raw = persona_data.get("opinions", {})

        return Persona(
            id=f"agent-{uuid.uuid4().hex[:8]}",
            name=name,
            age=max(18, min(85, age)),
            gender=gender,
            country=persona_data.get("country", random.choice(["DE", "CH", "AT"])),
            region=persona_data.get("region", "Zürich"),
            occupation=occupation,
            industry=entry.get("industry", ""),
            education=persona_data.get("education", ""),
            big_five=BigFive(
                openness=self._clamp(big_five_raw.get("openness", random.gauss(0.55, 0.2))),
                conscientiousness=self._clamp(big_five_raw.get("conscientiousness", random.gauss(0.6, 0.18))),
                extraversion=self._clamp(big_five_raw.get("extraversion", random.gauss(0.5, 0.22))),
                agreeableness=self._clamp(big_five_raw.get("agreeableness", random.gauss(0.58, 0.2))),
                neuroticism=self._clamp(big_five_raw.get("neuroticism", random.gauss(0.42, 0.22))),
            ),
            posting_style=PostingStyle(
                tone=style_raw.get("tone", random.choice(TONES)),
                frequency=style_raw.get("frequency", "weekly"),
                typical_topics=style_raw.get("typical_topics", []),
            ),
            opinions=OpinionSeeds(
                trust_institutions=self._clamp(opinions_raw.get("trust_institutions", 0.5)),
                environmental_concern=self._clamp(opinions_raw.get("environmental_concern", 0.5)),
                tech_optimism=self._clamp(opinions_raw.get("tech_optimism", 0.5)),
                economic_anxiety=self._clamp(opinions_raw.get("economic_anxiety", 0.5)),
                social_progressivism=self._clamp(opinions_raw.get("social_progressivism", 0.5)),
            ),
            interests=persona_data.get("interests", []),
            stakeholder_role=role,
            bio=persona_data.get("bio", f"{name}, {occupation}"),
        )

    def _generate_template_persona(self, role: str, rng: random.Random, index: int) -> Persona:
        """Generate a single persona instantly from templates. No LLM needed."""
        country = rng.choices(
            [c for c, _ in DACH_COUNTRY_DISTRIBUTION], weights=[w for _, w in DACH_COUNTRY_DISTRIBUTION]
        )[0]
        region = rng.choice(DACH_REGIONS[country])
        age_range = rng.choices(DACH_AGE_DISTRIBUTION, weights=[w for _, _, w in DACH_AGE_DISTRIBUTION])[0]
        age = rng.randint(age_range[0], age_range[1])
        gender = rng.choice(["male", "female"])

        # Pick a name from the pool
        first_name = rng.choice(DACH_FIRST_NAMES_M if gender == "male" else DACH_FIRST_NAMES_F)
        last_name = rng.choice(DACH_LAST_NAMES)
        name = f"{first_name} {last_name}"

        # Role-specific occupation
        occupation = rng.choice(ROLE_OCCUPATIONS.get(role, ["Angestellte/r"]))
        industry = ROLE_INDUSTRIES.get(role, "")

        # Varied Big Five (not all 0.5!)
        big_five = BigFive(
            openness=max(0, min(1, rng.gauss(0.55, 0.22))),
            conscientiousness=max(0, min(1, rng.gauss(0.60, 0.18))),
            extraversion=max(0, min(1, rng.gauss(0.50, 0.24))),
            agreeableness=max(0, min(1, rng.gauss(0.58, 0.20))),
            neuroticism=max(0, min(1, rng.gauss(0.42, 0.22))),
        )

        # Role-based opinions
        opinion_base = ROLE_OPINION_PROFILES.get(role, {})
        opinions = OpinionSeeds(
            trust_institutions=max(0, min(1, opinion_base.get("trust", 0.5) + rng.gauss(0, 0.15))),
            environmental_concern=max(0, min(1, opinion_base.get("env", 0.5) + rng.gauss(0, 0.15))),
            tech_optimism=max(0, min(1, opinion_base.get("tech", 0.5) + rng.gauss(0, 0.15))),
            economic_anxiety=max(0, min(1, opinion_base.get("econ", 0.5) + rng.gauss(0, 0.15))),
            social_progressivism=max(0, min(1, opinion_base.get("social", 0.5) + rng.gauss(0, 0.15))),
        )

        return Persona(
            id=f"agent-{uuid.uuid4().hex[:8]}",
            name=name,
            age=age,
            gender=gender,
            country=country,
            region=region,
            occupation=occupation,
            industry=industry,
            big_five=big_five,
            posting_style=PostingStyle(
                tone=rng.choice(TONES),
                frequency=rng.choice(FREQUENCIES),
            ),
            opinions=opinions,
            stakeholder_role=role,
            bio=f"{name}, {age}, {occupation} aus {region}.",
        )

    def _generate_fallback_batch(self, role: str, count: int) -> list[Persona]:
        """Generate simple personas without LLM (fallback for errors)."""
        personas = []
        for _ in range(count):
            country = random.choice(["DE", "CH", "AT"])
            region = random.choice(DACH_REGIONS[country])
            age_range = random.choices(
                DACH_AGE_DISTRIBUTION, weights=[w for _, _, w in DACH_AGE_DISTRIBUTION]
            )[0]
            age = random.randint(age_range[0], age_range[1])

            personas.append(
                Persona(
                    id=f"agent-{uuid.uuid4().hex[:8]}",
                    name=f"Agent {uuid.uuid4().hex[:6]}",
                    age=age,
                    gender=random.choice(["male", "female"]),
                    country=country,
                    region=region,
                    occupation="Angestellte/r",
                    big_five=BigFive(
                        openness=random.gauss(0.55, 0.20),
                        conscientiousness=random.gauss(0.62, 0.18),
                        extraversion=random.gauss(0.50, 0.22),
                        agreeableness=random.gauss(0.60, 0.18),
                        neuroticism=random.gauss(0.45, 0.22),
                    ),
                    posting_style=PostingStyle(
                        tone=random.choice(TONES),
                        frequency=random.choice(FREQUENCIES),
                    ),
                    stakeholder_role=role,
                )
            )
        return personas

    def _get_stakeholder_mix(self, scenario_type: str, total: int) -> dict[str, int]:
        """Calculate persona counts per stakeholder role."""
        template = STAKEHOLDER_TEMPLATES.get(scenario_type, STAKEHOLDER_TEMPLATES["default"])
        mix = {}
        assigned = 0
        roles = list(template.items())

        for role, pct in roles[:-1]:
            count = round(total * pct)
            mix[role] = count
            assigned += count

        # Last role gets the remainder
        last_role = roles[-1][0]
        mix[last_role] = total - assigned

        return mix

    @staticmethod
    def _assign_tiers(personas: list[Persona], dist: TierDistribution, rng: random.Random) -> None:
        """Assign agent tiers based on distribution."""
        n = len(personas)
        tier_counts = {
            AgentTier.POWER_CREATOR: round(n * dist.power_creator),
            AgentTier.ACTIVE_RESPONDER: round(n * dist.active_responder),
            AgentTier.SELECTIVE_ENGAGER: round(n * dist.selective_engager),
        }
        tier_counts[AgentTier.OBSERVER] = n - sum(tier_counts.values())

        # Shuffle personas to randomize tier assignment
        indices = list(range(n))
        rng.shuffle(indices)

        idx = 0
        for tier, count in tier_counts.items():
            for _ in range(count):
                if idx < n:
                    personas[indices[idx]].agent_tier = tier
                    idx += 1

    @staticmethod
    def _assign_special_flags(personas: list[Persona], rng: random.Random) -> None:
        """Assign zealot (5-10%) and contrarian (5%) flags."""
        n = len(personas)
        n_zealots = max(1, round(n * 0.07))
        n_contrarians = max(1, round(n * 0.05))

        indices = list(range(n))
        rng.shuffle(indices)

        for i in indices[:n_zealots]:
            personas[i].is_zealot = True
        for i in indices[n_zealots : n_zealots + n_contrarians]:
            personas[i].is_contrarian = True

    def _scale_personas(self, base: list[Persona], target: int, rng: random.Random) -> list[Persona]:
        """Scale base personas to target count via parametric variation."""
        result = list(base)

        while len(result) < target:
            source = rng.choice(base)
            variant = self._create_variant(source, rng)
            result.append(variant)

        return result[:target]

    def _create_variant(self, source: Persona, rng: random.Random) -> Persona:
        """Create a parametric variant of a base persona."""
        variant = deepcopy(source)
        variant.id = f"agent-{uuid.uuid4().hex[:8]}"

        # Vary age ±5
        variant.age = max(18, min(85, source.age + rng.randint(-5, 5)))

        # Vary Big Five with gaussian noise (std=0.08)
        variant.big_five = BigFive(
            openness=self._clamp(source.big_five.openness + rng.gauss(0, 0.08)),
            conscientiousness=self._clamp(source.big_five.conscientiousness + rng.gauss(0, 0.08)),
            extraversion=self._clamp(source.big_five.extraversion + rng.gauss(0, 0.08)),
            agreeableness=self._clamp(source.big_five.agreeableness + rng.gauss(0, 0.08)),
            neuroticism=self._clamp(source.big_five.neuroticism + rng.gauss(0, 0.08)),
        )

        # Vary opinions with slightly more noise (std=0.10)
        variant.opinions = OpinionSeeds(
            trust_institutions=self._clamp(source.opinions.trust_institutions + rng.gauss(0, 0.10)),
            environmental_concern=self._clamp(source.opinions.environmental_concern + rng.gauss(0, 0.10)),
            tech_optimism=self._clamp(source.opinions.tech_optimism + rng.gauss(0, 0.10)),
            economic_anxiety=self._clamp(source.opinions.economic_anxiety + rng.gauss(0, 0.10)),
            social_progressivism=self._clamp(source.opinions.social_progressivism + rng.gauss(0, 0.10)),
        )

        # Occasionally shift posting frequency (20%)
        if rng.random() < 0.20:
            variant.posting_style = PostingStyle(
                tone=source.posting_style.tone,
                frequency=rng.choice(FREQUENCIES),
                typical_topics=source.posting_style.typical_topics,
            )

        # Occasionally shift tone (15%)
        if rng.random() < 0.15:
            variant.posting_style = PostingStyle(
                tone=rng.choice(TONES),
                frequency=variant.posting_style.frequency,
                typical_topics=source.posting_style.typical_topics,
            )

        # Reset flags (will be reassigned)
        variant.is_zealot = False
        variant.is_contrarian = False

        return variant
