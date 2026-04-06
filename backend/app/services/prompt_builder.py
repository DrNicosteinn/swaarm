"""Prompt Builder — hybrid input pipeline.

Flow: User Freitext → LLM extracts structure → identifies gaps → suggests improvements
→ User confirms → Simulation starts.

Also determines scenario controversity and injects seed posts.
"""

import json

from loguru import logger
from pydantic import BaseModel, Field

from app.llm.base import LLMProvider, LLMResponse


class StructuredScenario(BaseModel):
    """Structured representation of a user's scenario input."""

    # Extracted fields
    industry: str = ""
    company: str = ""
    target_audience: str = ""
    market: str = ""  # DE, CH, AT, DACH
    statement: str = ""
    context: str = ""
    scenario_type: str = "default"  # corporate_crisis, product_launch, employer_branding, default
    controversity_score: float = Field(
        default=0.5, ge=0.0, le=1.0, description="How controversial this scenario is"
    )

    # Completeness
    missing_fields: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)

    # For simulation
    seed_posts: list[str] = Field(
        default_factory=list, description="Initial posts to inject into the simulation"
    )
    stakeholder_hint: str = ""  # Hint for persona generator about key stakeholders


ANALYSIS_PROMPT = (
    "Du analysierst Kommunikationsszenarien für eine Social-Media-Simulation.\n\n"
    "Analysiere diesen Freitext und extrahiere die relevanten Informationen:\n\n"
    '"{user_input}"\n\n'
    "Antworte als JSON mit diesen Feldern:\n"
    "{{\n"
    '  "industry": "Branche (z.B. Versicherung, Pharma, Tech)",\n'
    '  "company": "Firmenname falls genannt",\n'
    '  "target_audience": "Zielgruppe",\n'
    '  "market": "Markt (DE, CH, AT, oder DACH)",\n'
    '  "statement": "Das Statement/die Kampagne die getestet werden soll",\n'
    '  "context": "Relevanter Kontext und Hintergründe",\n'
    '  "scenario_type": "corporate_crisis / product_launch / employer_branding / default",\n'
    '  "controversity_score": 0.0 bis 1.0 (wie kontrovers ist das Szenario?),\n'
    '  "missing_fields": ["Liste von fehlenden aber wichtigen Informationen"],\n'
    '  "suggestions": ["Konkrete Verbesserungsvorschläge für den Input"],\n'
    '  "seed_posts": ["2-3 realistische Posts die als Auslöser der Diskussion dienen"],\n'
    '  "stakeholder_hint": "Welche Stakeholder-Gruppen besonders relevant sind"\n'
    "}}\n\n"
    "WICHTIG:\n"
    "- seed_posts sollen wie echte Social-Media-Posts klingen\n"
    "- Der erste seed_post sollte das offizielle Statement sein\n"
    "- Weitere seed_posts: eine erste Reaktion, evtl. ein Medienbericht\n"
    "- controversity_score: 0.0-0.3=routine, 0.3-0.6=standard, 0.6-1.0=krise\n"
    "- Sei konkret bei Vorschlägen was fehlt"
)

IMPROVEMENT_PROMPT = (
    "Du bist ein Kommunikationsexperte der einen Simulationsinput verbessert.\n\n"
    "Aktuelles Szenario:\n"
    "- Branche: {industry}\n"
    "- Firma: {company}\n"
    "- Zielgruppe: {target_audience}\n"
    "- Markt: {market}\n"
    "- Statement: {statement}\n"
    "- Kontext: {context}\n\n"
    "Was fehlt noch für eine realistische Simulation? "
    "Gib 3-5 konkrete Fragen die der Nutzer beantworten sollte.\n"
    "Antworte als JSON-Array von Strings."
)


class PromptBuilder:
    """Analyzes user input and builds structured simulation scenarios."""

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def analyze_input(self, raw_text: str) -> StructuredScenario:
        """Analyze free-text input and extract structured scenario.

        This is the main entry point. The user types their scenario,
        the LLM extracts structure and identifies gaps.
        """
        prompt = ANALYSIS_PROMPT.format(user_input=raw_text[:2000])

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Low temperature for consistent extraction
                max_tokens=1000,
            )

            scenario = self._parse_scenario_response(response)
            logger.info(
                f"Scenario analyzed: type={scenario.scenario_type}, "
                f"controversity={scenario.controversity_score:.1f}, "
                f"missing={len(scenario.missing_fields)}"
            )
            return scenario

        except Exception as e:
            logger.error(f"Input analysis failed: {e}")
            # Return a minimal scenario with everything marked as missing
            return StructuredScenario(
                statement=raw_text[:500],
                missing_fields=["Branche", "Zielgruppe", "Markt", "Kontext"],
                suggestions=["Bitte gib mehr Details zu deinem Szenario an."],
            )

    async def suggest_improvements(self, scenario: StructuredScenario) -> list[str]:
        """Generate improvement suggestions for an incomplete scenario."""
        prompt = IMPROVEMENT_PROMPT.format(
            industry=scenario.industry or "nicht angegeben",
            company=scenario.company or "nicht angegeben",
            target_audience=scenario.target_audience or "nicht angegeben",
            market=scenario.market or "nicht angegeben",
            statement=scenario.statement[:300] or "nicht angegeben",
            context=scenario.context[:300] or "nicht angegeben",
        )

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=500,
            )

            content = response.content or "[]"
            start = content.find("[")
            end = content.rfind("]") + 1
            if start >= 0 and end > 0:
                suggestions = json.loads(content[start:end])
                return [str(s) for s in suggestions[:5]]
        except Exception as e:
            logger.warning(f"Improvement suggestions failed: {e}")

        return scenario.suggestions

    def get_controversity_level(self, score: float) -> str:
        """Map controversity score to level string."""
        if score >= 0.6:
            return "crisis"
        if score >= 0.3:
            return "standard"
        return "routine"

    def _parse_scenario_response(self, response: LLMResponse) -> StructuredScenario:
        """Parse LLM response into a StructuredScenario."""
        content = response.content or "{}"

        # Extract JSON from response
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            return StructuredScenario(
                missing_fields=["Konnte den Input nicht analysieren"],
            )

        try:
            data = json.loads(content[start:end])
            return StructuredScenario(
                industry=data.get("industry", ""),
                company=data.get("company", ""),
                target_audience=data.get("target_audience", ""),
                market=data.get("market", ""),
                statement=data.get("statement", ""),
                context=data.get("context", ""),
                scenario_type=data.get("scenario_type", "default"),
                controversity_score=max(0.0, min(1.0, float(data.get("controversity_score", 0.5)))),
                missing_fields=data.get("missing_fields", []),
                suggestions=data.get("suggestions", []),
                seed_posts=data.get("seed_posts", []),
                stakeholder_hint=data.get("stakeholder_hint", ""),
            )
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning(f"Failed to parse scenario JSON: {e}")
            return StructuredScenario(
                missing_fields=["JSON-Parsing fehlgeschlagen"],
            )
