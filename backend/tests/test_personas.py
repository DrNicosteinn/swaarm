"""Tests for persona generator."""

import json
import random

import pytest

from app.llm.base import LLMProvider, LLMResponse
from app.models.persona import AgentTier, BigFive, Persona, PostingStyle
from app.models.simulation import ScenarioControversity
from app.simulation.personas import PersonaGenerationConfig, PersonaGenerator


class MockPersonaLLM(LLMProvider):
    """Mock LLM that returns realistic persona JSON."""

    async def chat(self, messages, tools=None, temperature=0.7, max_tokens=500) -> LLMResponse:
        # Return a batch of 3 test personas
        personas = [
            {
                "name": "Claudia Meier",
                "age": 38,
                "gender": "female",
                "country": "CH",
                "region": "Zürich",
                "occupation": "Produktmanagerin",
                "industry": "Versicherung",
                "education": "Uni St. Gallen",
                "sinus_milieu": "Performer",
                "big_five": {
                    "openness": 0.7,
                    "conscientiousness": 0.8,
                    "extraversion": 0.4,
                    "agreeableness": 0.6,
                    "neuroticism": 0.3,
                },
                "posting_style": {
                    "tone": "sachlich",
                    "frequency": "weekly",
                    "typical_topics": ["Versicherung", "Digitalisierung"],
                },
                "opinions": {
                    "trust_institutions": 0.7,
                    "environmental_concern": 0.6,
                    "tech_optimism": 0.8,
                    "economic_anxiety": 0.3,
                    "social_progressivism": 0.5,
                },
                "interests": ["FinTech", "Wandern", "Innovation"],
                "bio": "Claudia arbeitet seit 10 Jahren in der Versicherungsbranche.",
            },
            {
                "name": "Max Richter",
                "age": 31,
                "gender": "male",
                "country": "DE",
                "region": "Berlin",
                "occupation": "Tech-Journalist",
                "industry": "Medien",
                "education": "FU Berlin",
                "sinus_milieu": "Expeditives",
                "big_five": {
                    "openness": 0.9,
                    "conscientiousness": 0.5,
                    "extraversion": 0.7,
                    "agreeableness": 0.3,
                    "neuroticism": 0.5,
                },
                "posting_style": {
                    "tone": "provokativ",
                    "frequency": "daily",
                    "typical_topics": ["KI", "Digitalpolitik"],
                },
                "opinions": {
                    "trust_institutions": 0.3,
                    "environmental_concern": 0.5,
                    "tech_optimism": 0.7,
                    "economic_anxiety": 0.4,
                    "social_progressivism": 0.8,
                },
                "interests": ["Netzpolitik", "Startups", "Podcasts"],
                "bio": "Max schreibt für t3n und Heise über Tech-Themen.",
            },
            {
                "name": "Lisa Hofer",
                "age": 42,
                "gender": "female",
                "country": "AT",
                "region": "Wien",
                "occupation": "HR-Managerin",
                "industry": "Tech",
                "education": "WU Wien",
                "sinus_milieu": "Adaptiv-Pragmatische Mitte",
                "big_five": {
                    "openness": 0.6,
                    "conscientiousness": 0.7,
                    "extraversion": 0.6,
                    "agreeableness": 0.8,
                    "neuroticism": 0.4,
                },
                "posting_style": {
                    "tone": "empathisch",
                    "frequency": "weekly",
                    "typical_topics": ["HR", "NewWork"],
                },
                "opinions": {
                    "trust_institutions": 0.6,
                    "environmental_concern": 0.7,
                    "tech_optimism": 0.6,
                    "economic_anxiety": 0.5,
                    "social_progressivism": 0.7,
                },
                "interests": ["Coaching", "Arbeitsrecht", "Reisen"],
                "bio": "Lisa leitet People & Culture bei einem Wiener Tech-Startup.",
            },
        ]
        return LLMResponse(
            content=json.dumps(personas),
            input_tokens=800,
            output_tokens=1200,
            model="mock",
        )

    async def generate_simple(self, prompt, temperature=0.7) -> str:
        return "mock"


@pytest.fixture
def generator():
    llm = MockPersonaLLM()
    return PersonaGenerator(llm)


class TestPersonaGenerator:
    @pytest.mark.asyncio
    async def test_generate_basic(self, generator):
        """Generate personas and verify basic properties."""
        config = PersonaGenerationConfig(
            scenario_text="SwissBank Entlassungen",
            scenario_type="corporate_crisis",
            target_count=10,
            base_persona_count=10,
            batch_size=3,
            seed=42,
        )
        personas = await generator.generate(config)

        assert len(personas) == 10
        assert all(isinstance(p, Persona) for p in personas)

    @pytest.mark.asyncio
    async def test_personas_have_unique_ids(self, generator):
        """All personas must have unique IDs."""
        config = PersonaGenerationConfig(
            scenario_text="Test",
            target_count=15,
            base_persona_count=10,
            batch_size=3,
            seed=42,
        )
        personas = await generator.generate(config)
        ids = [p.id for p in personas]
        assert len(ids) == len(set(ids))

    @pytest.mark.asyncio
    async def test_stakeholder_roles_assigned(self, generator):
        """Personas get stakeholder roles from the template."""
        config = PersonaGenerationConfig(
            scenario_text="Produktlaunch",
            scenario_type="product_launch",
            target_count=20,
            base_persona_count=20,
            batch_size=3,
            seed=42,
        )
        personas = await generator.generate(config)
        roles = {p.stakeholder_role for p in personas}
        assert len(roles) > 1  # Multiple stakeholder types

    @pytest.mark.asyncio
    async def test_tiers_assigned(self, generator):
        """Agent tiers are assigned based on controversity."""
        config = PersonaGenerationConfig(
            scenario_text="Krise",
            controversity=ScenarioControversity.CRISIS,
            target_count=50,
            base_persona_count=20,
            batch_size=3,
            seed=42,
        )
        personas = await generator.generate(config)
        tiers = [p.agent_tier for p in personas]

        # Crisis should have more creators and responders
        creators = sum(1 for t in tiers if t == AgentTier.POWER_CREATOR)
        observers = sum(1 for t in tiers if t == AgentTier.OBSERVER)
        assert creators > 0
        assert observers < len(personas) * 0.5  # Less than 50% observers in crisis

    @pytest.mark.asyncio
    async def test_zealots_and_contrarians(self, generator):
        """Zealots and contrarians are assigned."""
        config = PersonaGenerationConfig(
            scenario_text="Test",
            target_count=100,
            base_persona_count=30,
            batch_size=3,
            seed=42,
        )
        personas = await generator.generate(config)

        zealots = sum(1 for p in personas if p.is_zealot)
        contrarians = sum(1 for p in personas if p.is_contrarian)

        assert zealots > 0
        assert contrarians > 0
        # No overlap
        assert not any(p.is_zealot and p.is_contrarian for p in personas)

    @pytest.mark.asyncio
    async def test_scaling_creates_variants(self, generator):
        """When target > base, parametric variation creates variants."""
        config = PersonaGenerationConfig(
            scenario_text="Test",
            target_count=30,
            base_persona_count=10,
            batch_size=3,
            seed=42,
        )
        personas = await generator.generate(config)
        assert len(personas) == 30

        # IDs must be unique even though variants share source names
        ids = [p.id for p in personas]
        assert len(set(ids)) == 30

    @pytest.mark.asyncio
    async def test_big_five_values_valid(self, generator):
        """All Big Five values must be between 0 and 1."""
        config = PersonaGenerationConfig(
            scenario_text="Test",
            target_count=20,
            base_persona_count=10,
            batch_size=3,
            seed=42,
        )
        personas = await generator.generate(config)

        for p in personas:
            assert 0 <= p.big_five.openness <= 1
            assert 0 <= p.big_five.conscientiousness <= 1
            assert 0 <= p.big_five.extraversion <= 1
            assert 0 <= p.big_five.agreeableness <= 1
            assert 0 <= p.big_five.neuroticism <= 1

    @pytest.mark.asyncio
    async def test_cost_tracked(self, generator):
        """LLM usage is tracked during generation."""
        config = PersonaGenerationConfig(
            scenario_text="Test",
            target_count=10,
            base_persona_count=10,
            batch_size=3,
            seed=42,
        )
        await generator.generate(config)
        assert generator.usage.total_calls > 0
        assert generator.usage.total_input_tokens > 0


class TestStakeholderMix:
    def test_corporate_crisis_mix(self):
        gen = PersonaGenerator(MockPersonaLLM())
        mix = gen._get_stakeholder_mix("corporate_crisis", 100)
        assert sum(mix.values()) == 100
        assert "employees" in mix
        assert "customers" in mix
        assert "media" in mix

    def test_default_mix(self):
        gen = PersonaGenerator(MockPersonaLLM())
        mix = gen._get_stakeholder_mix("unknown_type", 50)
        assert sum(mix.values()) == 50

    def test_product_launch_mix(self):
        gen = PersonaGenerator(MockPersonaLLM())
        mix = gen._get_stakeholder_mix("product_launch", 200)
        assert sum(mix.values()) == 200
        assert mix.get("target_customers", 0) > mix.get("media", 0)


class TestParametricVariation:
    def test_variant_has_different_id(self):
        gen = PersonaGenerator(MockPersonaLLM())
        source = _make_test_persona()
        rng = random.Random(42)
        variant = gen._create_variant(source, rng)
        assert variant.id != source.id

    def test_variant_age_differs(self):
        gen = PersonaGenerator(MockPersonaLLM())
        source = _make_test_persona()
        # Run multiple variants — at least one should differ
        ages = set()
        for seed in range(20):
            variant = gen._create_variant(source, random.Random(seed))
            ages.add(variant.age)
        assert len(ages) > 1  # Not all same age

    def test_variant_big_five_differs(self):
        gen = PersonaGenerator(MockPersonaLLM())
        source = _make_test_persona()
        variant = gen._create_variant(source, random.Random(42))
        # At least one Big Five value should differ
        source_vals = [
            source.big_five.openness,
            source.big_five.conscientiousness,
            source.big_five.extraversion,
            source.big_five.agreeableness,
            source.big_five.neuroticism,
        ]
        variant_vals = [
            variant.big_five.openness,
            variant.big_five.conscientiousness,
            variant.big_five.extraversion,
            variant.big_five.agreeableness,
            variant.big_five.neuroticism,
        ]
        assert source_vals != variant_vals


def _make_test_persona() -> Persona:

    return Persona(
        id="test-source",
        name="Test Person",
        age=35,
        gender="female",
        country="CH",
        region="Zürich",
        occupation="Testperson",
        big_five=BigFive(
            openness=0.6, conscientiousness=0.5, extraversion=0.5, agreeableness=0.5, neuroticism=0.5
        ),
        posting_style=PostingStyle(tone="sachlich", frequency="weekly"),
        stakeholder_role="general",
    )
