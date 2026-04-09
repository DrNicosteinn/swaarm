"""Smart Decision Engine — analyzes user input and decides simulation strategy.

Sits between PromptBuilder (scenario extraction) and PersonaGenerator (persona creation).
Single LLM call that produces a complete simulation blueprint:
  - Input classification (what kind of simulation?)
  - Entity extraction with importance scoring
  - Web enrichment decisions (which entities are worth researching?)
  - Persona generation strategy (real vs role-based vs generated)

Usage:
    engine = SmartDecisionEngine(llm)
    decision = await engine.analyze(user_input, structured_scenario)
    # decision contains everything needed to configure persona generation
"""

import json
from enum import StrEnum

from loguru import logger
from pydantic import BaseModel, Field

from app.llm.base import LLMProvider, LLMUsageTracker

# ── Classification Types ──────────────────────────────────────────────


class SimulationType(StrEnum):
    """What kind of simulation the user needs."""

    CAMPAIGN_PRETEST = "campaign_pretest"  # Full document, stakeholders, maybe real entities
    QUICK_QUESTION = "quick_question"  # Short question, generic personas suffice
    STRATEGY_VALIDATION = "strategy_validation"  # Professional network, role-based personas
    CRISIS_COMMUNICATION = "crisis_communication"  # Media, employees, public — time-sensitive
    REPUTATION_CHECK = "reputation_check"  # How is entity X perceived? Needs real context
    POLICY_IMPACT = "policy_impact"  # Regulatory / political — needs institutional actors


class EntityType(StrEnum):
    """Classification of extracted entities."""

    REAL_PERSON = "real_person"  # Named public figure (CEO, politician, journalist)
    REAL_COMPANY = "real_company"  # Named organization
    ROLE = "role"  # Generic role (e.g. "Kunden", "Mitarbeiter")
    INSTITUTION = "institution"  # Government body, regulator, NGO
    MEDIA_OUTLET = "media_outlet"  # Named media (NZZ, Spiegel, etc.)
    PRODUCT = "product"  # Named product or brand
    EVENT = "event"  # Named event (Davos, COP28, etc.)


class EnrichmentDecision(StrEnum):
    """Whether to web-enrich an entity."""

    ENRICH = "enrich"  # Worth a web search (~$0.01, ~2s)
    SKIP = "skip"  # Not worth enriching
    OPTIONAL = "optional"  # Enrich if budget allows


# ── Output Models ─────────────────────────────────────────────────────


class EntityRelationship(BaseModel):
    """A directed relationship between two entities."""

    target_entity_name: str
    relation_type: str = Field(
        description="e.g. 'leadership', 'employment', 'competition', 'customer', 'regulatory'"
    )
    label: str = Field(description="Human-readable label, e.g. 'ist CEO von', 'konkurriert mit'")
    strength: float = Field(default=0.5, ge=0.0, le=1.0)


class ExtractedEntity(BaseModel):
    """An entity extracted from user input with importance scoring."""

    name: str
    entity_type: EntityType
    importance: float = Field(ge=0.0, le=1.0, description="0.0 = barely mentioned, 1.0 = central to scenario")
    role_in_scenario: str = Field(
        description="What role this entity plays (e.g. 'Absender der Kommunikation', 'Betroffener')"
    )
    enrichment: EnrichmentDecision = EnrichmentDecision.SKIP
    enrichment_reason: str = ""
    persona_count: int = Field(
        default=1,
        ge=0,
        description="How many personas to create for this entity. 0 = context only, no persona.",
    )

    # Dynamic sub-type assigned by LLM (e.g. "CEO", "Tech-Journalist", "Langzeit-Kunde")
    sub_type: str = ""
    # Estimated sentiment toward the scenario (-1.0 = strongly against, +1.0 = strongly for)
    sentiment_toward_scenario: float = Field(default=0.0, ge=-1.0, le=1.0)
    # Text snippet where entity was found/mentioned
    context_snippet: str = ""
    # Relationships to other entities
    relationships: list[EntityRelationship] = Field(default_factory=list)


class PersonaStrategy(BaseModel):
    """How to compose the persona population."""

    real_persona_count: int = Field(
        default=0, description="Personas based on real, named entities (web-enriched)"
    )
    role_based_count: int = Field(
        default=0, description="Personas based on specific roles (LLM-generated with role context)"
    )
    generated_count: int = Field(default=0, description="Generic personas from demographic distributions")
    total: int = Field(default=0)

    # Role distribution for generated personas
    role_distribution: dict[str, float] = Field(
        default_factory=dict,
        description="Role -> percentage for generated personas (e.g. {'customers': 0.3, 'media': 0.05})",
    )

    # Platform recommendation
    recommended_platform: str = Field(
        default="public", description="'public' (Twitter-like) or 'professional' (LinkedIn-like)"
    )

    # Controversity assessment
    estimated_controversity: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How controversial the topic is (affects agent tier distribution)",
    )


class SimulationDecision(BaseModel):
    """Complete output of the smart decision engine."""

    # Classification
    simulation_type: SimulationType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="Brief explanation of the classification")

    # Extracted entities
    entities: list[ExtractedEntity] = Field(default_factory=list)

    # Enrichment summary
    entities_to_enrich: list[str] = Field(
        default_factory=list, description="Names of entities that should be web-enriched"
    )
    estimated_enrichment_cost_usd: float = 0.0
    estimated_enrichment_time_seconds: float = 0.0

    # Persona strategy
    persona_strategy: PersonaStrategy = Field(default_factory=PersonaStrategy)

    # Scenario refinements (passed downstream)
    scenario_type: str = "default"  # Maps to STAKEHOLDER_TEMPLATES key
    key_themes: list[str] = Field(default_factory=list)
    simulation_focus: str = Field(
        default="", description="What the simulation should specifically measure/observe"
    )

    # Follow-up questions when context is incomplete
    follow_up_questions: list[str] = Field(
        default_factory=list,
        description="2-4 specific questions to fill context gaps, shown as guided input to user",
    )

    # Human-readable scenario summary for the confirmation screen
    scenario_summary: str = Field(
        default="", description="1-2 sentence summary of the understood scenario, in German"
    )


# ── The Prompt ────────────────────────────────────────────────────────

DECISION_SYSTEM_PROMPT = """\
Du bist der Strategie-Entscheider fuer eine KI-Simulations-Plattform die oeffentliche Reaktionen \
auf Unternehmenskommunikation simuliert. Deine Aufgabe: Analysiere den User-Input und erstelle \
einen vollstaendigen Simulationsplan.

## Deine Entscheidungen

### 1. SIMULATION_TYPE — Was fuer eine Simulation braucht der User?

- campaign_pretest: Komplettes Dokument/Statement das getestet werden soll
- quick_question: Kurze Frage, keine spezifischen Stakeholder
- strategy_validation: LinkedIn/Professional-Kontext, Employer Branding
- crisis_communication: Krise, Shitstorm, Skandal, Entlassungen
- reputation_check: Wie wird Person X / Firma Y wahrgenommen?
- policy_impact: Regulierung, Politik, Gesetze

### 2. ENTITY EXTRACTION — Wer ist relevant?

Extrahiere ALLE genannten Entitaeten und bewerte ihre Wichtigkeit:

**Importance-Score Regeln:**
- 1.0: Absender der Kommunikation (die Firma/Person die kommuniziert)
- 0.8-0.9: Direkt betroffene Parteien (Mitarbeiter bei Entlassungen, Kunden bei Produktrueckruf)
- 0.6-0.7: Schluesselstakeholder (Investoren, Regulatoren, wichtige Partner)
- 0.4-0.5: Kontextrelevante Akteure (Wettbewerber, Medien, Experten)
- 0.1-0.3: Am Rande erwaehnte Entitaeten

**Entity Types (feste Basis-Types):**
- real_person: Namentlich genannte oeffentliche Person
- real_company: Namentlich genannte Organisation
- role: Generische Rolle (z.B. "Kunden", "Mitarbeiter")
- institution: Behoerde, Regulator, NGO
- media_outlet: Namentlich genanntes Medium
- product: Namentlich genanntes Produkt/Marke
- event: Namentlich genanntes Ereignis

**Sub-Types (dynamisch, kontextspezifisch):**
Vergib jedem Entity einen spezifischen sub_type, z.B.:
- real_person → "CEO", "Politiker", "Tech-Journalist", "Influencer"
- real_company → "Pharmakonzern", "Startup", "Beratungsfirma"
- role → "Langzeit-Kunde", "Betroffener Mitarbeiter", "Branchenexperte"

**Sentiment (Haltung zum Szenario):**
Schaetze die Haltung jeder Entity zum Szenario ein:
- -1.0: Stark dagegen / kritisch (z.B. Gewerkschaft bei Entlassungen)
- 0.0: Neutral / unklar
- +1.0: Stark dafuer / unterstuetzend (z.B. Firma die kommuniziert)

**Beziehungen zwischen Entities:**
Erkenne und benenne Beziehungen zwischen extrahierten Entities:
- Beziehungstypen: leadership, employment, competition, customer, regulatory, partnership, opposition
- Labels auf Deutsch: "ist CEO von", "arbeitet bei", "konkurriert mit", "reguliert", "ist Kunde von"
- Nur relevante Beziehungen die fuer die Simulation wichtig sind

### 3. WEB ENRICHMENT — Wen lohnt es sich zu recherchieren?

Jede Web-Suche kostet ~$0.01 und dauert ~2 Sekunden. Entscheide klug:

**ENRICH wenn:**
- Oeffentliche Person mit relevanter Meinung zum Thema (CEO, Politiker, Journalist)
- Firma die kuerzlich in den Nachrichten war zum selben Thema
- Institution deren offizielle Position wichtig ist
- Maximum: 10-15 Entitaeten pro Simulation

**SKIP wenn:**
- Generische Rollen ("Kunden", "Mitarbeiter")
- Firmen/Personen die nur am Rande erwaehnt werden (importance < 0.4)
- Allgemein bekannte Entitaeten wo Web-Recherche wenig Neues bringt
- Produkte oder Events (diese werden anders kontextualisiert)

**OPTIONAL wenn:**
- Mittelwichtige Akteure (importance 0.4-0.6)
- Wettbewerber (nuetzlich aber nicht kritisch)

### 4. PERSONA STRATEGY — Wie setzt sich die Simulation zusammen?

**Drei Persona-Kategorien:**
1. **Real Personas** (max ~10%): Basierend auf realen Entitaeten.
   Nur fuer importance >= 0.7 UND entity_type real_person/real_company.
2. **Role-Based Personas** (max ~25%): LLM-generiert mit Rollenkontext.
   Fuer identifizierte Rollen und Stakeholder-Gruppen.
3. **Generated Personas** (~65-85%): Aus demographischen Verteilungen.
   Fuellung fuer realistische Populationsgroesse.

**Persona-Counts pro Entity:**
- real_person mit importance >= 0.8: 1 Persona (die Person selbst)
- real_company mit importance >= 0.8: 3-5 Personas (CEO, Sprecher, Mitarbeiter)
- role mit importance >= 0.6: 5-20 Personas je nach Wichtigkeit
- role mit importance < 0.6: 2-5 Personas
- Entitaet mit importance < 0.3: 0 Personas (nur Kontext)

**Platform-Empfehlung:**
- "public" (Twitter/X-like): Standard fuer die meisten Szenarien
- "professional" (LinkedIn-like): Employer Branding, B2B, Karriere-Themen

### 5. FOLLOW-UP QUESTIONS — Was fehlt noch?

Falls der User-Input wichtigen Kontext vermissen laesst, generiere 2-4 spezifische \
Fragen auf Deutsch. Die Fragen sollen einem nicht-technischen User helfen, besseren \
Kontext zu liefern. Beispiele:
- "In welcher Branche ist euer Unternehmen taetig?"
- "Wer ist die Hauptzielgruppe eurer Kommunikation?"
- "Gibt es bekannte Kritiker oder Wettbewerber die reagieren koennten?"
- "Wurde das Thema bereits in den Medien diskutiert?"

Wenn der Input bereits vollstaendig ist, gib eine leere Liste zurueck.

### 6. SCENARIO SUMMARY — Zusammenfassung

Fasse das verstandene Szenario in 1-2 Saetzen auf Deutsch zusammen. \
Diese Zusammenfassung wird dem User zur Bestaetigung angezeigt bevor die Simulation startet."""

DECISION_USER_PROMPT = """\
Analysiere diesen Input und erstelle den Simulationsplan.

## User-Input:
\"\"\"{user_input}\"\"\"

{structured_context}

## Antwort-Format

Antworte NUR mit diesem JSON (kein anderer Text):

{{
  "simulation_type": "campaign_pretest|quick_question|...",
  "confidence": 0.0-1.0,
  "reasoning": "Kurze Begruendung der Klassifikation",
  "scenario_summary": "1-2 Saetze Zusammenfassung auf Deutsch",

  "entities": [
    {{
      "name": "Name der Entitaet",
      "entity_type": "real_person|real_company|role|institution|media_outlet|product|event",
      "sub_type": "Spezifischer Unter-Typ (z.B. CEO, Tech-Journalist, Langzeit-Kunde)",
      "importance": 0.0-1.0,
      "sentiment_toward_scenario": -1.0 bis 1.0,
      "role_in_scenario": "Rolle im Szenario",
      "context_snippet": "Relevante Textstelle aus dem Input",
      "enrichment": "enrich|skip|optional",
      "enrichment_reason": "Warum enrichen/nicht enrichen",
      "persona_count": 0-20,
      "relationships": [
        {{
          "target_entity_name": "Name der Ziel-Entity",
          "relation_type": "leadership|employment|competition|customer|regulatory|partnership|opposition",
          "label": "ist CEO von / arbeitet bei / konkurriert mit",
          "strength": 0.0-1.0
        }}
      ]
    }}
  ],

  "persona_strategy": {{
    "real_persona_count": 0,
    "role_based_count": 0,
    "generated_count": 0,
    "total": 0,
    "role_distribution": {{
      "customers": 0.30,
      "employees": 0.15,
      "media": 0.05,
      "general_public": 0.30,
      "...": 0.20
    }},
    "recommended_platform": "public|professional",
    "estimated_controversity": 0.0-1.0
  }},

  "scenario_type": "corporate_crisis|product_launch|employer_branding|default",
  "key_themes": ["Thema 1", "Thema 2"],
  "simulation_focus": "Was die Simulation speziell messen/beobachten soll",
  "follow_up_questions": ["Frage 1 auf Deutsch", "Frage 2 auf Deutsch"]
}}"""

# ── Few-Shot Examples ─────────────────────────────────────────────────

FEW_SHOT_EXAMPLES = [
    # Example 1: Campaign Pre-test (like toxic.fm coffee campaign)
    {
        "role": "user",
        "content": (
            "Analysiere diesen Input und erstelle den Simulationsplan.\n\n"
            "## User-Input:\n"
            '"""toxic.fm, ein Berliner Podcast-Startup, plant eine Kampagne fuer ihren neuen '
            '"Rage Brew" Kaffee. Der Slogan lautet "Kaffee der so toxisch ist wie dein Ex". '
            "CEO Lisa Neumann will wissen ob der Humor ankommt oder einen Shitstorm ausloest. "
            'Die Zielgruppe sind 20-35 jaehrige Social-Media-affine Millennials und Gen Z."""\n\n'
        ),
    },
    {
        "role": "assistant",
        "content": json.dumps(
            {
                "simulation_type": "campaign_pretest",
                "confidence": 0.95,
                "reasoning": "Kampagne soll vor Veroeffentlichung getestet werden. Provokanter Slogan.",
                "scenario_summary": "toxic.fm will testen, ob ihr provokanter Kaffee-Slogan bei der Gen-Z-Zielgruppe ankommt oder einen Shitstorm ausloest.",
                "entities": [
                    {
                        "name": "toxic.fm",
                        "entity_type": "real_company",
                        "sub_type": "Podcast-Startup",
                        "importance": 1.0,
                        "sentiment_toward_scenario": 1.0,
                        "role_in_scenario": "Absender der Kampagne",
                        "context_snippet": "toxic.fm, ein Berliner Podcast-Startup, plant eine Kampagne",
                        "enrichment": "enrich",
                        "enrichment_reason": "Startup mit oeffentlichem Profil",
                        "persona_count": 3,
                        "relationships": [],
                    },
                    {
                        "name": "Lisa Neumann",
                        "entity_type": "real_person",
                        "sub_type": "CEO",
                        "importance": 0.8,
                        "sentiment_toward_scenario": 0.9,
                        "role_in_scenario": "CEO und Gesicht der Kampagne",
                        "context_snippet": "CEO Lisa Neumann will wissen ob der Humor ankommt",
                        "enrichment": "enrich",
                        "enrichment_reason": "CEO einer oeffentlichen Firma, oeffentliche Aussagen relevant",
                        "persona_count": 1,
                        "relationships": [
                            {
                                "target_entity_name": "toxic.fm",
                                "relation_type": "leadership",
                                "label": "ist CEO von",
                                "strength": 1.0,
                            }
                        ],
                    },
                    {
                        "name": "Rage Brew",
                        "entity_type": "product",
                        "sub_type": "Kaffeeprodukt",
                        "importance": 0.7,
                        "sentiment_toward_scenario": 0.0,
                        "role_in_scenario": "Das beworbene Produkt",
                        "context_snippet": "neuen Rage Brew Kaffee",
                        "enrichment": "skip",
                        "enrichment_reason": "Neues Produkt, noch keine oeffentlichen Informationen",
                        "persona_count": 0,
                        "relationships": [
                            {
                                "target_entity_name": "toxic.fm",
                                "relation_type": "partnership",
                                "label": "ist Produkt von",
                                "strength": 0.8,
                            }
                        ],
                    },
                    {
                        "name": "Social-Media-affine Millennials/Gen Z",
                        "entity_type": "role",
                        "sub_type": "Zielgruppen-Segment",
                        "importance": 0.9,
                        "sentiment_toward_scenario": 0.0,
                        "role_in_scenario": "Primaere Zielgruppe",
                        "context_snippet": "20-35 jaehrige Social-Media-affine Millennials und Gen Z",
                        "enrichment": "skip",
                        "enrichment_reason": "Generische Zielgruppe, braucht demographische Generierung",
                        "persona_count": 15,
                        "relationships": [],
                    },
                    {
                        "name": "Feministische Aktivist:innen",
                        "entity_type": "role",
                        "sub_type": "Aktivisten-Gruppe",
                        "importance": 0.6,
                        "sentiment_toward_scenario": -0.7,
                        "role_in_scenario": "Potenzielle Kritiker des 'toxischer Ex'-Slogans",
                        "context_snippet": "",
                        "enrichment": "skip",
                        "enrichment_reason": "Generische Rolle",
                        "persona_count": 5,
                        "relationships": [],
                    },
                ],
                "persona_strategy": {
                    "real_persona_count": 4,
                    "role_based_count": 25,
                    "generated_count": 71,
                    "total": 100,
                    "role_distribution": {
                        "target_customers": 0.35,
                        "general_public": 0.25,
                        "media": 0.05,
                        "influencers": 0.10,
                        "activists": 0.08,
                        "competitors": 0.05,
                        "company_employees": 0.07,
                        "marketing_experts": 0.05,
                    },
                    "recommended_platform": "public",
                    "estimated_controversity": 0.65,
                },
                "scenario_type": "product_launch",
                "key_themes": [
                    "Geschmacksgrenzen im Marketing",
                    "Toxische Beziehungen als Humor",
                    "Gen-Z-Humor vs. gesellschaftliche Sensibilitaet",
                ],
                "simulation_focus": "Kipppunkt zwischen lustig-provokant und geschmacklos identifizieren.",
                "follow_up_questions": [],
            },
            ensure_ascii=False,
        ),
    },
    # Example 2: Quick Question
    {
        "role": "user",
        "content": (
            "Analysiere diesen Input und erstelle den Simulationsplan.\n\n"
            "## User-Input:\n"
            '"""Wie wuerde die Schweizer Oeffentlichkeit auf ein generelles Tempolimit von '
            '120 km/h auf Autobahnen reagieren?"""\n\n'
        ),
    },
    {
        "role": "assistant",
        "content": json.dumps(
            {
                "simulation_type": "quick_question",
                "confidence": 0.90,
                "reasoning": "Kurze hypothetische Frage ohne spezifische Firma. Braucht breite Meinungen.",
                "scenario_summary": "Simulation der oeffentlichen Reaktion auf ein generelles Tempolimit von 120 km/h auf Schweizer Autobahnen.",
                "entities": [
                    {
                        "name": "Schweizer Bevoelkerung",
                        "entity_type": "role",
                        "sub_type": "Allgemeine Oeffentlichkeit",
                        "importance": 0.9,
                        "sentiment_toward_scenario": 0.0,
                        "role_in_scenario": "Betroffene Oeffentlichkeit",
                        "context_snippet": "Schweizer Oeffentlichkeit",
                        "enrichment": "skip",
                        "enrichment_reason": "Generische Bevoelkerung",
                        "persona_count": 0,
                        "relationships": [],
                    },
                    {
                        "name": "TCS (Touring Club Schweiz)",
                        "entity_type": "institution",
                        "sub_type": "Autofahrer-Lobby",
                        "importance": 0.6,
                        "sentiment_toward_scenario": -0.6,
                        "role_in_scenario": "Wichtigste Autofahrer-Lobby",
                        "context_snippet": "",
                        "enrichment": "optional",
                        "enrichment_reason": "Offizielle Position zum Tempolimit waere nuetzlich",
                        "persona_count": 2,
                        "relationships": [],
                    },
                    {
                        "name": "UVEK/ASTRA",
                        "entity_type": "institution",
                        "sub_type": "Bundesbehoerde",
                        "importance": 0.5,
                        "sentiment_toward_scenario": 0.3,
                        "role_in_scenario": "Zustaendige Bundesbehoerde",
                        "context_snippet": "",
                        "enrichment": "skip",
                        "enrichment_reason": "Allgemein bekannte Position",
                        "persona_count": 1,
                        "relationships": [
                            {
                                "target_entity_name": "TCS (Touring Club Schweiz)",
                                "relation_type": "regulatory",
                                "label": "reguliert Strassenverkehr gemeinsam mit",
                                "strength": 0.4,
                            }
                        ],
                    },
                ],
                "persona_strategy": {
                    "real_persona_count": 0,
                    "role_based_count": 15,
                    "generated_count": 85,
                    "total": 100,
                    "role_distribution": {
                        "autofahrer": 0.30,
                        "umweltbewusste": 0.15,
                        "pendler": 0.15,
                        "general_public": 0.25,
                        "politiker": 0.05,
                        "media": 0.05,
                        "transportbranche": 0.05,
                    },
                    "recommended_platform": "public",
                    "estimated_controversity": 0.55,
                },
                "scenario_type": "default",
                "key_themes": [
                    "Persoenliche Freiheit vs. Sicherheit",
                    "Umweltschutz",
                    "Pendler-Alltag",
                ],
                "simulation_focus": "Sentiment-Verteilung und Hauptargumente beider Seiten identifizieren.",
                "follow_up_questions": [
                    "Gibt es einen konkreten Anlass fuer die Diskussion (z.B. ein politischer Vorstoss)?",
                    "Soll die Simulation die gesamte Schweiz abdecken oder einen bestimmten Kanton?",
                ],
            },
            ensure_ascii=False,
        ),
    },
    # Example 3: Crisis Communication
    {
        "role": "user",
        "content": (
            "Analysiere diesen Input und erstelle den Simulationsplan.\n\n"
            "## User-Input:\n"
            '"""Novartis plant den Abbau von 800 Stellen am Standort Basel. '
            "Die interne Kommunikation soll morgen frueh rausgehen, "
            "die Pressemitteilung um 10 Uhr. Wie reagieren Mitarbeiter, Medien und Politik? "
            'Der CEO Vas Narasimhan wird das Statement persoenlich machen."""\n\n'
        ),
    },
    {
        "role": "assistant",
        "content": json.dumps(
            {
                "simulation_type": "crisis_communication",
                "confidence": 0.98,
                "reasoning": "Massiver Stellenabbau, zeitkritisch. Klassische Krisenkommunikation.",
                "scenario_summary": "Novartis baut 800 Stellen in Basel ab. CEO Vas Narasimhan kommuniziert persoenlich. Simulation testet Reaktionen von Mitarbeitern, Medien und Politik.",
                "entities": [
                    {
                        "name": "Novartis",
                        "entity_type": "real_company",
                        "sub_type": "Pharmakonzern",
                        "importance": 1.0,
                        "sentiment_toward_scenario": 0.3,
                        "role_in_scenario": "Absender — das Unternehmen das Stellen abbaut",
                        "context_snippet": "Novartis plant den Abbau von 800 Stellen am Standort Basel",
                        "enrichment": "enrich",
                        "enrichment_reason": "Boersennotiert, aktuelle Strategie relevant",
                        "persona_count": 5,
                        "relationships": [],
                    },
                    {
                        "name": "Vas Narasimhan",
                        "entity_type": "real_person",
                        "sub_type": "CEO",
                        "importance": 0.9,
                        "sentiment_toward_scenario": 0.5,
                        "role_in_scenario": "CEO der das Statement macht — wird persoenlich bewertet",
                        "context_snippet": "Der CEO Vas Narasimhan wird das Statement persoenlich machen",
                        "enrichment": "enrich",
                        "enrichment_reason": "CEO, oeffentliche Person, Kommunikation relevant",
                        "persona_count": 1,
                        "relationships": [
                            {
                                "target_entity_name": "Novartis",
                                "relation_type": "leadership",
                                "label": "ist CEO von",
                                "strength": 1.0,
                            }
                        ],
                    },
                    {
                        "name": "Novartis-Mitarbeiter Basel",
                        "entity_type": "role",
                        "sub_type": "Betroffene Angestellte",
                        "importance": 0.95,
                        "sentiment_toward_scenario": -0.8,
                        "role_in_scenario": "Direkt Betroffene — 800 potenzielle Kuendigungen",
                        "context_snippet": "Abbau von 800 Stellen",
                        "enrichment": "skip",
                        "enrichment_reason": "Generische Gruppe, braucht rollenbasierte Generierung",
                        "persona_count": 15,
                        "relationships": [
                            {
                                "target_entity_name": "Novartis",
                                "relation_type": "employment",
                                "label": "arbeiten bei",
                                "strength": 1.0,
                            }
                        ],
                    },
                    {
                        "name": "Basler Zeitung",
                        "entity_type": "media_outlet",
                        "sub_type": "Regionalzeitung",
                        "importance": 0.6,
                        "sentiment_toward_scenario": -0.2,
                        "role_in_scenario": "Lokale Berichterstattung",
                        "context_snippet": "",
                        "enrichment": "optional",
                        "enrichment_reason": "Relevante lokale Berichterstattung zu Novartis",
                        "persona_count": 1,
                        "relationships": [],
                    },
                    {
                        "name": "Unia (Gewerkschaft)",
                        "entity_type": "institution",
                        "sub_type": "Gewerkschaft",
                        "importance": 0.7,
                        "sentiment_toward_scenario": -0.9,
                        "role_in_scenario": "Arbeitnehmervertretung — wird protestieren",
                        "context_snippet": "",
                        "enrichment": "enrich",
                        "enrichment_reason": "Offizielle Position zu Novartis-Stellenabbau relevant",
                        "persona_count": 2,
                        "relationships": [
                            {
                                "target_entity_name": "Novartis-Mitarbeiter Basel",
                                "relation_type": "partnership",
                                "label": "vertritt Interessen von",
                                "strength": 0.8,
                            }
                        ],
                    },
                    {
                        "name": "Basler Regierungsrat",
                        "entity_type": "institution",
                        "sub_type": "Kantonale Regierung",
                        "importance": 0.6,
                        "sentiment_toward_scenario": -0.4,
                        "role_in_scenario": "Regionale Politik — Arbeitsplaetze im Kanton",
                        "context_snippet": "",
                        "enrichment": "optional",
                        "enrichment_reason": "Politische Reaktion relevant aber vorhersehbar",
                        "persona_count": 2,
                        "relationships": [
                            {
                                "target_entity_name": "Novartis",
                                "relation_type": "regulatory",
                                "label": "ist Standort-Regierung fuer",
                                "strength": 0.5,
                            }
                        ],
                    },
                    {
                        "name": "Roche",
                        "entity_type": "real_company",
                        "sub_type": "Pharmakonzern",
                        "importance": 0.3,
                        "sentiment_toward_scenario": 0.0,
                        "role_in_scenario": "Wettbewerber am gleichen Standort — Vergleichspunkt",
                        "context_snippet": "",
                        "enrichment": "skip",
                        "enrichment_reason": "Nur am Rande relevant",
                        "persona_count": 0,
                        "relationships": [
                            {
                                "target_entity_name": "Novartis",
                                "relation_type": "competition",
                                "label": "konkurriert mit",
                                "strength": 0.7,
                            }
                        ],
                    },
                ],
                "persona_strategy": {
                    "real_persona_count": 8,
                    "role_based_count": 30,
                    "generated_count": 162,
                    "total": 200,
                    "role_distribution": {
                        "employees": 0.20,
                        "former_employees": 0.05,
                        "customers": 0.10,
                        "media": 0.05,
                        "politicians": 0.05,
                        "investors": 0.05,
                        "general_public": 0.30,
                        "activists": 0.05,
                        "pharma_experten": 0.05,
                        "gewerkschaft": 0.05,
                        "anwohner_basel": 0.05,
                    },
                    "recommended_platform": "public",
                    "estimated_controversity": 0.85,
                },
                "scenario_type": "corporate_crisis",
                "key_themes": [
                    "Arbeitsplatzabbau in der Schweiz",
                    "Pharma-Standort Basel",
                    "CEO-Verantwortung",
                    "Sozialplan und Abfindungen",
                ],
                "simulation_focus": "CEO-Bewertung, Stimmungskippe, dominante Narrative nach 24h.",
                "follow_up_questions": [],
            },
            ensure_ascii=False,
        ),
    },
]


# ── Engine ────────────────────────────────────────────────────────────


class SmartDecisionEngine:
    """Analyzes user input and produces a complete simulation strategy.

    One LLM call with few-shot examples. Output is a structured
    SimulationDecision that feeds into PersonaGenerator and SimulationEngine.
    """

    def __init__(self, llm: LLMProvider, usage_tracker: LLMUsageTracker | None = None):
        self.llm = llm
        self.usage = usage_tracker or LLMUsageTracker()

    async def analyze(
        self,
        user_input: str,
        structured_scenario: dict | None = None,
        target_agent_count: int = 200,
    ) -> SimulationDecision:
        """Analyze user input and return a complete simulation decision.

        Args:
            user_input: Raw user text (document, question, or scenario description).
            structured_scenario: Optional pre-extracted scenario from PromptBuilder.
            target_agent_count: Desired total agent count (adjusts persona_strategy.total).

        Returns:
            SimulationDecision with classification, entities, enrichment plan, and persona strategy.
        """
        # Build structured context hint if PromptBuilder already ran
        structured_context = ""
        if structured_scenario:
            parts = []
            for key in ("company", "industry", "market", "scenario_type", "controversity_score"):
                val = structured_scenario.get(key)
                if val:
                    parts.append(f"- {key}: {val}")
            if parts:
                structured_context = "## Bereits extrahierter Kontext:\n" + "\n".join(parts)

        user_prompt = DECISION_USER_PROMPT.format(
            user_input=user_input[:50000],
            structured_context=structured_context,
        )

        # Build messages: system + few-shot examples + actual query
        messages = [
            {"role": "system", "content": DECISION_SYSTEM_PROMPT},
            *FEW_SHOT_EXAMPLES,
            {"role": "user", "content": user_prompt},
        ]

        try:
            response = await self.llm.chat(
                messages=messages,
                temperature=0.3,
                max_tokens=4000,
            )
            self.usage.record(response)

            decision = self._parse_response(response.content or "{}")

            # Post-process: adjust counts to match target_agent_count
            decision = self._adjust_counts(decision, target_agent_count)

            # Post-process: compute enrichment cost/time estimates
            decision = self._compute_enrichment_estimates(decision)

            logger.info(
                f"Smart decision: type={decision.simulation_type}, "
                f"entities={len(decision.entities)}, "
                f"enrich={len(decision.entities_to_enrich)}, "
                f"strategy={decision.persona_strategy.real_persona_count}/"
                f"{decision.persona_strategy.role_based_count}/"
                f"{decision.persona_strategy.generated_count}"
            )

            return decision

        except Exception as e:
            logger.error(f"Smart decision failed: {e}")
            return self._fallback_decision(user_input, target_agent_count)

    def _parse_response(self, content: str) -> SimulationDecision:
        """Parse the LLM JSON response into a SimulationDecision."""
        start = content.find("{")
        end = content.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in response")

        data = json.loads(content[start:end])

        # Parse entities
        entities = []
        for raw in data.get("entities", []):
            try:
                # Parse relationships
                relationships = []
                for rel_raw in raw.get("relationships", []):
                    try:
                        relationships.append(
                            EntityRelationship(
                                target_entity_name=rel_raw["target_entity_name"],
                                relation_type=rel_raw.get("relation_type", ""),
                                label=rel_raw.get("label", ""),
                                strength=max(0.0, min(1.0, float(rel_raw.get("strength", 0.5)))),
                            )
                        )
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Failed to parse relationship: {e}")

                entities.append(
                    ExtractedEntity(
                        name=raw["name"],
                        entity_type=EntityType(raw["entity_type"]),
                        importance=max(0.0, min(1.0, float(raw.get("importance", 0.5)))),
                        role_in_scenario=raw.get("role_in_scenario", ""),
                        enrichment=EnrichmentDecision(raw.get("enrichment", "skip")),
                        enrichment_reason=raw.get("enrichment_reason", ""),
                        persona_count=max(0, int(raw.get("persona_count", 1))),
                        sub_type=raw.get("sub_type", ""),
                        sentiment_toward_scenario=max(
                            -1.0, min(1.0, float(raw.get("sentiment_toward_scenario", 0.0)))
                        ),
                        context_snippet=raw.get("context_snippet", ""),
                        relationships=relationships,
                    )
                )
            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse entity: {e}")
                continue

        # Parse persona strategy
        strat_raw = data.get("persona_strategy", {})
        persona_strategy = PersonaStrategy(
            real_persona_count=strat_raw.get("real_persona_count", 0),
            role_based_count=strat_raw.get("role_based_count", 0),
            generated_count=strat_raw.get("generated_count", 0),
            total=strat_raw.get("total", 100),
            role_distribution=strat_raw.get("role_distribution", {}),
            recommended_platform=strat_raw.get("recommended_platform", "public"),
            estimated_controversity=max(0.0, min(1.0, float(strat_raw.get("estimated_controversity", 0.5)))),
        )

        # Collect entities to enrich
        entities_to_enrich = [e.name for e in entities if e.enrichment == EnrichmentDecision.ENRICH]

        return SimulationDecision(
            simulation_type=SimulationType(data.get("simulation_type", "quick_question")),
            confidence=max(0.0, min(1.0, float(data.get("confidence", 0.5)))),
            reasoning=data.get("reasoning", ""),
            entities=entities,
            entities_to_enrich=entities_to_enrich,
            persona_strategy=persona_strategy,
            scenario_type=data.get("scenario_type", "default"),
            key_themes=data.get("key_themes", []),
            simulation_focus=data.get("simulation_focus", ""),
            follow_up_questions=data.get("follow_up_questions", []),
            scenario_summary=data.get("scenario_summary", ""),
        )

    def _adjust_counts(self, decision: SimulationDecision, target_count: int) -> SimulationDecision:
        """Scale persona counts to match the target agent count.

        Preserves the ratio between real/role-based/generated while
        hitting the target total exactly. The LLM decides the mix freely.
        """
        strat = decision.persona_strategy
        current_total = strat.real_persona_count + strat.role_based_count + strat.generated_count
        if current_total == 0:
            current_total = 1

        # Calculate ratios from LLM decision (no caps — LLM decides freely)
        real_ratio = strat.real_persona_count / current_total
        role_ratio = strat.role_based_count / current_total

        real_count = int(real_ratio * target_count)
        role_count = int(role_ratio * target_count)
        generated_count = target_count - real_count - role_count

        strat.real_persona_count = real_count
        strat.role_based_count = role_count
        strat.generated_count = generated_count
        strat.total = target_count

        return decision

    def _compute_enrichment_estimates(self, decision: SimulationDecision) -> SimulationDecision:
        """Compute cost and time estimates for web enrichment."""
        enrich_count = len(decision.entities_to_enrich)

        # Cost: ~$0.01 per search (Brave/Serper API)
        decision.estimated_enrichment_cost_usd = round(enrich_count * 0.01, 3)

        # Time: ~2 seconds per search (parallelized in batches of 5)
        batches = -(-enrich_count // 5)  # ceil division
        decision.estimated_enrichment_time_seconds = round(batches * 2.0, 1)

        return decision

    def _fallback_decision(self, user_input: str, target_count: int) -> SimulationDecision:
        """Produce a safe fallback decision when the LLM call fails."""
        # Simple heuristic: long input = campaign pretest, short = quick question
        is_long = len(user_input) > 500
        sim_type = SimulationType.CAMPAIGN_PRETEST if is_long else SimulationType.QUICK_QUESTION

        return SimulationDecision(
            simulation_type=sim_type,
            confidence=0.3,
            reasoning="Fallback — LLM-Analyse fehlgeschlagen, konservative Defaults",
            entities=[],
            entities_to_enrich=[],
            persona_strategy=PersonaStrategy(
                real_persona_count=0,
                role_based_count=int(target_count * 0.20),
                generated_count=int(target_count * 0.80),
                total=target_count,
                role_distribution={
                    "general_public": 0.35,
                    "supporters": 0.20,
                    "critics": 0.20,
                    "media": 0.05,
                    "influencers": 0.05,
                    "neutral_observers": 0.15,
                },
                recommended_platform="public",
                estimated_controversity=0.5,
            ),
            scenario_type="default",
            key_themes=[],
            simulation_focus="Allgemeine Sentiment-Analyse",
        )
