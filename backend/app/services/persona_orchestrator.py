"""Persona Orchestrator — plans the entire persona ecosystem using GPT-4.1.

Takes entities + enrichment data and produces a detailed persona plan where
every persona has a clear role, relationship to entities, and reason to exist.

Three phases:
  1. PLAN: GPT-4.1 designs the full persona ecosystem
  2. DISCOVER: Identifies new entities to research (competitors, key figures)
  3. VALIDATE: Reviews generated personas and fixes relationships

Usage:
    orchestrator = PersonaOrchestrator(llm_orchestrator, llm_fast)
    plan = await orchestrator.plan_personas(decision, enrichment_results, scenario)
    # plan contains every persona with their entity link and relationships
"""

import json

from loguru import logger
from pydantic import BaseModel, Field

from app.llm.base import LLMProvider, LLMResponse, LLMUsageTracker
from app.services.entity_enricher import EnrichmentResult
from app.services.smart_decision import ExtractedEntity, SimulationDecision


# ── Output Models ────────────────────────────────────────────────────


class PlannedPersona(BaseModel):
    """A persona planned by the orchestrator."""

    name: str
    role: str  # e.g. "employees", "media", "competitor_employee"
    occupation: str
    age: int = 35
    gender: str = "female"
    # Link to entity
    linked_entity: str = ""  # Name of the entity this persona belongs to
    relationship_to_entity: str = ""  # e.g. "arbeitet bei", "berichtet ueber", "ist Kunde von"
    # Additional relationships to other personas
    relationships: list[dict] = Field(default_factory=list)  # [{target_name, label}]
    # Why this persona exists
    reasoning: str = ""
    # Source
    persona_type: str = "generated"  # "real_enriched", "real_minimal", "role_based", "generated"
    needs_enrichment: bool = False  # Should this persona be web-searched?
    sentiment_bias: float = 0.0  # -1 to +1 toward the scenario


class NewEntityToResearch(BaseModel):
    """An entity the orchestrator wants to research that wasn't in the original input."""

    name: str
    entity_type: str  # "real_person", "real_company", "institution"
    sub_type: str = ""
    reason: str = ""  # Why this entity should be researched
    search_query: str = ""  # Optimized search query for Serper


class PersonaPlan(BaseModel):
    """Complete persona ecosystem plan."""

    personas: list[PlannedPersona] = Field(default_factory=list)
    new_entities_to_research: list[NewEntityToResearch] = Field(default_factory=list)
    total_planned: int = 0
    reasoning: str = ""  # Overall reasoning for the plan


# ── Prompts ──────────────────────────────────────────────────────────

ORCHESTRATOR_SYSTEM_PROMPT = """\
Du bist ein Experte fuer Stakeholder-Analyse und Social-Media-Simulation. \
Deine Aufgabe ist es, ein realistisches Persona-Oekosystem fuer eine Simulation \
zu planen, in der getestet wird, wie die Oeffentlichkeit auf eine Unternehmensmitteilung reagiert.

## Deine Aufgabe

Du bekommst:
1. Ein Szenario (was passiert)
2. Bereits erkannte Entities (Firmen, Personen, Rollen)
3. Web-Recherche-Ergebnisse zu diesen Entities

Du planst:
- JEDE einzelne Persona die in der Simulation vorkommen soll
- Ihre Verbindung zu den Entities
- Ihre Beziehungen zueinander
- Warum sie relevant ist

## Regeln fuer gute Personas

1. **Jede Persona braucht einen Grund:** Keine generischen "Person 47". \
   Jede Persona hat eine klare Rolle und Verbindung zum Szenario.

2. **Realistische Verteilung:** Nicht 50% Politiker. Denke an:
   - Direkt Betroffene (Mitarbeiter, Kunden) = groesster Anteil
   - Indirekt Betroffene (Lieferanten, Partner, Nachbarn)
   - Meinungsmacher (Journalisten, Influencer, Experten)
   - Institutionelle Akteure (Gewerkschaften, Behoerden, Politiker)
   - Allgemeine Oeffentlichkeit (Buerger mit Meinung)

3. **Beziehungsnetz:** Personas sind nicht isoliert. Beispiele:
   - Mitarbeiter A ist verheiratet mit Lehrerin B (die sich Sorgen macht)
   - Journalist C hat letzte Woche ueber die Firma berichtet
   - Kunde D hat gerade einen Vertrag unterschrieben
   - Konkurrent-Mitarbeiter E versucht Novartis-Leute abzuwerben

4. **Echte Personas vorschlagen:** Wenn ein Konkurrent relevant ist, \
   nenne den echten Konkurrenznamen und schlage vor ihn zu googeln. \
   Wenn ein bekannter Journalist relevant ist, nenne ihn.

5. **DACH-Kontext:** Realistische Namen, Regionen, Berufe fuer \
   Deutschland, Schweiz, Oesterreich.

6. **Sentiment-Verteilung:** Nicht alle negativ! Es gibt immer:
   - Kritiker (negativ)
   - Unterstuetzer/Versteher (positiv)
   - Neutrale Beobachter
   - Die Verteilung haengt vom Szenario ab.

## Neue Entities vorschlagen

Wenn du merkst dass wichtige Akteure fehlen (z.B. der Hauptkonkurrent, \
ein relevanter Politiker, eine wichtige Institution), schlage sie als \
"new_entities_to_research" vor. Diese werden dann gegoogelt.

Maximum 5 neue Entities."""

ORCHESTRATOR_USER_PROMPT = """\
## Szenario
{scenario}

## Bereits erkannte Entities
{entities_description}

## Web-Recherche-Ergebnisse
{enrichment_description}

## Gewuenschte Persona-Anzahl
{target_count} Personas total

## Aufgabe
Plane das gesamte Persona-Oekosystem. Jede Persona muss:
- Einen realistischen DACH-Namen haben
- Eine klare Rolle und Verbindung zu mindestens einer Entity haben
- Einen Grund haben warum sie in dieser Simulation relevant ist

Antworte NUR mit diesem JSON:
{{
  "reasoning": "Kurze Erklaerung der Gesamtstrategie (2-3 Saetze)",
  "new_entities_to_research": [
    {{
      "name": "Name der Entity",
      "entity_type": "real_person|real_company|institution",
      "sub_type": "z.B. Pharmakonzern, Journalist",
      "reason": "Warum diese Entity recherchiert werden sollte",
      "search_query": "Optimierte Google-Suche"
    }}
  ],
  "personas": [
    {{
      "name": "Realistischer Name",
      "role": "stakeholder_rolle",
      "occupation": "Konkreter Beruf",
      "age": 35,
      "gender": "male|female",
      "linked_entity": "Name der verbundenen Entity",
      "relationship_to_entity": "arbeitet bei / berichtet ueber / ist Kunde von",
      "relationships": [
        {{"target_name": "Name einer anderen Persona", "label": "ist verheiratet mit / kennt / konkurriert mit"}}
      ],
      "reasoning": "Warum diese Persona relevant ist (1 Satz)",
      "persona_type": "real_enriched|role_based|generated",
      "needs_enrichment": true/false,
      "sentiment_bias": -1.0 bis 1.0
    }}
  ]
}}"""

VALIDATION_PROMPT = """\
Du bist ein Qualitaetskontrolleur fuer Persona-Simulationen. \
Pruefe diesen Persona-Plan und korrigiere Probleme.

## Szenario
{scenario}

## Aktueller Persona-Plan ({count} Personas)
{personas_summary}

## Pruefe und korrigiere:

1. **Fehlende Verbindungen:** Haben alle Personas eine linked_entity? \
   Gibt es Personas die isoliert sind?
2. **Unrealistische Verteilung:** Sind zu viele Personas vom gleichen Typ? \
   (z.B. 50% Politiker waere unrealistisch)
3. **Fehlende Perspektiven:** Fehlen wichtige Stakeholder-Gruppen? \
   (z.B. Kunden, Lieferanten, Anwohner)
4. **Beziehungsqualitaet:** Sind die Beziehungen sinnvoll? \
   Gibt es Personas die mehr Beziehungen haben sollten?
5. **Sentiment-Balance:** Ist die Sentiment-Verteilung realistisch?

Antworte NUR mit JSON:
{{
  "issues_found": ["Issue 1", "Issue 2"],
  "fixes": [
    {{
      "persona_name": "Name",
      "action": "update_link|add_relationship|change_sentiment|remove",
      "details": {{}}
    }}
  ],
  "missing_personas": [
    {{
      "name": "Neuer Name",
      "role": "rolle",
      "occupation": "Beruf",
      "age": 35,
      "gender": "female",
      "linked_entity": "Entity-Name",
      "relationship_to_entity": "Beziehung",
      "reasoning": "Warum diese Persona fehlt",
      "sentiment_bias": 0.0
    }}
  ]
}}"""


# ── Service ──────────────────────────────────────────────────────────


class PersonaOrchestrator:
    """Plans the entire persona ecosystem using a powerful LLM."""

    def __init__(
        self,
        llm_orchestrator: LLMProvider,
        llm_fast: LLMProvider,
        usage_tracker: LLMUsageTracker | None = None,
    ):
        self.llm = llm_orchestrator  # GPT-4.1 for planning
        self.llm_fast = llm_fast  # GPT-4o-mini for individual persona details
        self.usage = usage_tracker or LLMUsageTracker()

    async def plan_personas(
        self,
        decision: SimulationDecision,
        enrichment_results: list[EnrichmentResult],
        scenario_text: str,
        target_count: int = 200,
    ) -> PersonaPlan:
        """Phase 1: Plan the entire persona ecosystem.

        Uses GPT-4.1 to create a detailed plan where every persona
        has a clear role, entity link, and relationships.
        """
        # Build entity descriptions for the prompt
        entities_desc = self._format_entities(decision.entities)
        enrichment_desc = self._format_enrichments(enrichment_results)

        user_prompt = ORCHESTRATOR_USER_PROMPT.format(
            scenario=scenario_text[:5000],
            entities_description=entities_desc,
            enrichment_description=enrichment_desc,
            target_count=target_count,
        )

        logger.info(f"Orchestrator planning {target_count} personas...")

        try:
            response = await self.llm.chat(
                messages=[
                    {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=8000,  # Enough for ~25 personas with relationships
            )
            self.usage.record(response)

            plan = self._parse_plan(response.content or "{}", target_count)

            logger.info(
                f"Orchestrator planned {len(plan.personas)} personas, "
                f"{len(plan.new_entities_to_research)} new entities to research"
            )
            return plan

        except Exception as e:
            logger.error(f"Orchestrator planning failed: {e}")
            return self._fallback_plan(decision, target_count)

    async def validate_and_refine(
        self,
        plan: PersonaPlan,
        scenario_text: str,
    ) -> PersonaPlan:
        """Phase 3: Validate the plan and fix issues.

        Uses GPT-4.1 to review all personas, check relationships,
        and add missing perspectives.
        """
        # Build summary of current plan
        personas_summary = self._format_plan_summary(plan)

        prompt = VALIDATION_PROMPT.format(
            scenario=scenario_text[:3000],
            count=len(plan.personas),
            personas_summary=personas_summary,
        )

        logger.info(f"Validating persona plan ({len(plan.personas)} personas)...")

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=8000,
            )
            self.usage.record(response)

            plan = self._apply_fixes(plan, response.content or "{}")
            return plan

        except Exception as e:
            logger.warning(f"Validation failed: {e}")
            return plan  # Return unmodified plan on failure

    def _format_entities(self, entities: list[ExtractedEntity]) -> str:
        """Format entities for the orchestrator prompt."""
        lines = []
        for e in entities:
            rels = ""
            if e.relationships:
                rels = " | Beziehungen: " + ", ".join(
                    f"{r.label} → {r.target_entity_name}" for r in e.relationships
                )
            lines.append(
                f"- {e.name} [{e.entity_type.value}, {e.sub_type}] "
                f"Wichtigkeit={e.importance}, Sentiment={e.sentiment_toward_scenario}, "
                f"Rolle: {e.role_in_scenario}{rels}"
            )
        return "\n".join(lines) if lines else "(Keine Entities erkannt)"

    def _format_enrichments(self, results: list[EnrichmentResult]) -> str:
        """Format enrichment results for the orchestrator prompt."""
        lines = []
        for r in results:
            if r.success:
                positions = ", ".join(r.known_positions[:3]) if r.known_positions else "unbekannt"
                lines.append(
                    f"- {r.entity_name}: {r.verified_title} bei {r.verified_company}. "
                    f"Stil: {r.communication_style}. "
                    f"Positionen: {positions}. "
                    f"Kontext: {r.recent_context[:200]}"
                )
            else:
                lines.append(f"- {r.entity_name}: Recherche fehlgeschlagen")
        return "\n".join(lines) if lines else "(Keine Recherche-Ergebnisse)"

    def _format_plan_summary(self, plan: PersonaPlan) -> str:
        """Format plan for validation prompt."""
        lines = []
        # Group by linked_entity
        by_entity: dict[str, list[PlannedPersona]] = {}
        for p in plan.personas:
            key = p.linked_entity or "(unverbunden)"
            by_entity.setdefault(key, []).append(p)

        for entity, personas in by_entity.items():
            lines.append(f"\n### {entity} ({len(personas)} Personas)")
            for p in personas[:10]:  # Limit for prompt size
                rels = ", ".join(f"{r['label']} → {r['target_name']}" for r in p.relationships[:2])
                lines.append(
                    f"  - {p.name} ({p.occupation}, {p.role}) Sentiment: {p.sentiment_bias:+.1f} | {rels}"
                )
            if len(personas) > 10:
                lines.append(f"  ... und {len(personas) - 10} weitere")

        # Sentiment distribution
        sentiments = [p.sentiment_bias for p in plan.personas]
        neg = sum(1 for s in sentiments if s < -0.2)
        pos = sum(1 for s in sentiments if s > 0.2)
        neu = len(sentiments) - neg - pos
        lines.append(f"\nSentiment-Verteilung: {neg} negativ, {neu} neutral, {pos} positiv")

        return "\n".join(lines)

    def _parse_plan(self, content: str, target_count: int) -> PersonaPlan:
        """Parse the orchestrator's JSON response."""
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON found in orchestrator response")

        data = json.loads(content[start:end])

        personas = []
        for raw in data.get("personas", []):
            try:
                personas.append(
                    PlannedPersona(
                        name=raw.get("name", "Unbekannt"),
                        role=raw.get("role", "general_public"),
                        occupation=raw.get("occupation", ""),
                        age=raw.get("age", 35),
                        gender=raw.get("gender", "female"),
                        linked_entity=raw.get("linked_entity", ""),
                        relationship_to_entity=raw.get("relationship_to_entity", ""),
                        relationships=raw.get("relationships", []),
                        reasoning=raw.get("reasoning", ""),
                        persona_type=raw.get("persona_type", "generated"),
                        needs_enrichment=raw.get("needs_enrichment", False),
                        sentiment_bias=max(-1, min(1, float(raw.get("sentiment_bias", 0)))),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse planned persona: {e}")

        new_entities = []
        for raw in data.get("new_entities_to_research", []):
            try:
                new_entities.append(
                    NewEntityToResearch(
                        name=raw.get("name", ""),
                        entity_type=raw.get("entity_type", "real_company"),
                        sub_type=raw.get("sub_type", ""),
                        reason=raw.get("reason", ""),
                        search_query=raw.get("search_query", raw.get("name", "")),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse new entity: {e}")

        return PersonaPlan(
            personas=personas,
            new_entities_to_research=new_entities[:5],
            total_planned=len(personas),
            reasoning=data.get("reasoning", ""),
        )

    def _apply_fixes(self, plan: PersonaPlan, content: str) -> PersonaPlan:
        """Apply validation fixes to the plan."""
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start == -1 or end == 0:
                return plan

            data = json.loads(content[start:end])

            issues = data.get("issues_found", [])
            if issues:
                logger.info(f"Validation found {len(issues)} issues: {issues}")

            # Apply fixes
            persona_map = {p.name: p for p in plan.personas}
            for fix in data.get("fixes", []):
                name = fix.get("persona_name", "")
                action = fix.get("action", "")
                details = fix.get("details", {})
                persona = persona_map.get(name)
                if not persona:
                    continue

                if action == "update_link":
                    persona.linked_entity = details.get("linked_entity", persona.linked_entity)
                    persona.relationship_to_entity = details.get(
                        "relationship_to_entity", persona.relationship_to_entity
                    )
                elif action == "add_relationship":
                    persona.relationships.append(details)
                elif action == "change_sentiment":
                    persona.sentiment_bias = float(details.get("sentiment_bias", persona.sentiment_bias))
                elif action == "remove":
                    plan.personas = [p for p in plan.personas if p.name != name]

            # Add missing personas
            for raw in data.get("missing_personas", []):
                try:
                    plan.personas.append(
                        PlannedPersona(
                            name=raw.get("name", ""),
                            role=raw.get("role", "general_public"),
                            occupation=raw.get("occupation", ""),
                            age=raw.get("age", 35),
                            gender=raw.get("gender", "female"),
                            linked_entity=raw.get("linked_entity", ""),
                            relationship_to_entity=raw.get("relationship_to_entity", ""),
                            reasoning=raw.get("reasoning", ""),
                            sentiment_bias=float(raw.get("sentiment_bias", 0)),
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to add missing persona: {e}")

            plan.total_planned = len(plan.personas)
            logger.info(f"Validation applied: {len(plan.personas)} personas after fixes")

        except Exception as e:
            logger.warning(f"Failed to apply validation fixes: {e}")

        return plan

    def _fallback_plan(self, decision: SimulationDecision, target_count: int) -> PersonaPlan:
        """Simple fallback if the orchestrator fails."""
        personas = []
        for entity in decision.entities:
            for i in range(min(entity.persona_count, 5)):
                personas.append(
                    PlannedPersona(
                        name=f"{entity.name} Persona {i + 1}",
                        role=entity.role_in_scenario,
                        occupation=entity.sub_type or "Angestellte/r",
                        linked_entity=entity.name,
                        relationship_to_entity="verbunden mit",
                        persona_type="role_based" if entity.entity_type.value == "role" else "generated",
                        sentiment_bias=entity.sentiment_toward_scenario,
                    )
                )
        return PersonaPlan(
            personas=personas[:target_count],
            total_planned=min(len(personas), target_count),
            reasoning="Fallback — Orchestrator fehlgeschlagen",
        )
