"""Persona generator — creates diverse, DACH-calibrated personas for simulation.

Pipeline:
1. Determine stakeholder mix from scenario
2. Generate ~500 base personas via LLM (batches of 10)
3. Scale to target count via parametric variation
"""

import json
import random
import uuid
from copy import deepcopy

from loguru import logger
from pydantic import BaseModel

from app.llm.base import LLMProvider, LLMUsageTracker
from app.models.persona import AgentTier, BigFive, OpinionSeeds, Persona, PostingStyle
from app.models.simulation import ScenarioControversity, TierDistribution

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

BATCH_GENERATION_PROMPT = (
    "Du generierst realistische Personas für eine "
    "Social-Media-Simulation im DACH-Raum.\n\n"
    "Erstelle genau {batch_size} Personas:\n"
    "- Stakeholder-Rolle: {role}\n"
    "- Szenario: {scenario}\n"
    "- Region: DACH\n\n"
    "{previous_hint}\n\n"
    "Antworte NUR mit einem JSON-Array. Jede Persona hat:\n"
    '{{"name":"DACH-Name","age":18-85,"gender":"male/female",'
    '"country":"DE/CH/AT","region":"Stadt",'
    '"occupation":"Beruf","industry":"Branche",'
    '"education":"Bildung","sinus_milieu":"Milieu",'
    '"big_five":{{"openness":0-1,"conscientiousness":0-1,'
    '"extraversion":0-1,"agreeableness":0-1,"neuroticism":0-1}},'
    '"posting_style":{{"tone":"sachlich/emotional/provokativ",'
    '"frequency":"daily/weekly/monthly/rarely",'
    '"typical_topics":["Themen"]}},'
    '"opinions":{{"trust_institutions":0-1,'
    '"environmental_concern":0-1,"tech_optimism":0-1,'
    '"economic_anxiety":0-1,"social_progressivism":0-1}},'
    '"interests":["3-5 Interessen"],'
    '"bio":"2-3 Sätze Beschreibung"}}\n\n'
    "WICHTIG:\n"
    "- Jede Persona EINZIGARTIG\n"
    "- Big Five NICHT alle um 0.5 — echte Variation!\n"
    "- Kulturell passende Namen\n"
    "- Keine Stereotypen"
)


class PersonaGenerationConfig(BaseModel):
    """Configuration for persona generation."""

    scenario_text: str
    scenario_type: str = "default"
    target_count: int = 200
    base_persona_count: int = 500
    controversity: ScenarioControversity = ScenarioControversity.STANDARD
    seed: int | None = None
    batch_size: int = 10


class PersonaGenerator:
    """Generates diverse, DACH-calibrated personas for simulation."""

    def __init__(self, llm: LLMProvider, usage_tracker: LLMUsageTracker | None = None):
        self.llm = llm
        self.usage = usage_tracker or LLMUsageTracker()

    async def generate(self, config: PersonaGenerationConfig) -> list[Persona]:
        """Generate personas for a simulation.

        1. Determine stakeholder mix
        2. Generate base personas via LLM (batches)
        3. Assign tiers based on controversity
        4. Scale to target count via parametric variation
        """
        rng = random.Random(config.seed)

        # Step 1: Determine how many personas per stakeholder role
        stakeholder_mix = self._get_stakeholder_mix(config.scenario_type, config.base_persona_count)
        logger.info(f"Stakeholder mix: {stakeholder_mix}")

        # Step 2: Generate base personas via LLM
        base_personas: list[Persona] = []
        for role, count in stakeholder_mix.items():
            if count == 0:
                continue
            n_batches = max(1, count // config.batch_size)
            remainder = count % config.batch_size

            for _batch_idx in range(n_batches):
                batch = await self._generate_batch(
                    role=role,
                    scenario=config.scenario_text,
                    batch_size=config.batch_size,
                    previous_names=[p.name for p in base_personas[-5:]],
                )
                base_personas.extend(batch)

            if remainder > 0:
                batch = await self._generate_batch(
                    role=role,
                    scenario=config.scenario_text,
                    batch_size=remainder,
                    previous_names=[p.name for p in base_personas[-5:]],
                )
                base_personas.extend(batch)

        logger.info(f"Generated {len(base_personas)} base personas via LLM")

        # Step 3: Assign tiers
        tier_dist = TierDistribution.for_controversity(config.controversity)
        self._assign_tiers(base_personas, tier_dist, rng)

        # Step 4: Assign zealot/contrarian flags
        self._assign_special_flags(base_personas, rng)

        # Step 5: Scale to target count if needed
        if config.target_count > len(base_personas):
            personas = self._scale_personas(base_personas, config.target_count, rng)
        else:
            personas = base_personas[: config.target_count]

        logger.info(
            f"Persona generation complete: {len(personas)} personas, "
            f"LLM cost: ${self.usage.total_cost_usd:.4f}"
        )

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
