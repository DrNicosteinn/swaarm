"""Tests for prompt builder."""

import json

import pytest

from app.llm.base import LLMProvider, LLMResponse
from app.services.prompt_builder import PromptBuilder, StructuredScenario


class MockAnalysisLLM(LLMProvider):
    """Mock LLM that returns structured scenario analysis."""

    async def chat(self, messages, tools=None, temperature=0.7, max_tokens=500) -> LLMResponse:
        content = messages[-1]["content"] if messages else ""

        # Improvement prompt starts with "Kommunikationsexperte"
        if "Kommunikationsexperte" in content:
            return LLMResponse(
                content=json.dumps(
                    [
                        "Welcher Tonfall soll das Statement haben?",
                        "Gibt es eine Vorgeschichte zu diesem Thema?",
                        "Wer sind die Hauptkritiker?",
                    ]
                ),
                input_tokens=300,
                output_tokens=100,
                model="mock",
            )

        # Default: return structured scenario
        return LLMResponse(
            content=json.dumps(
                {
                    "industry": "Finanzwesen",
                    "company": "SwissBank",
                    "target_audience": "Kunden und Mitarbeiter",
                    "market": "CH",
                    "statement": "Die Restrukturierung ist notwendig für die Zukunftsfähigkeit.",
                    "context": "200 Mitarbeiter werden entlassen.",
                    "scenario_type": "corporate_crisis",
                    "controversity_score": 0.8,
                    "missing_fields": ["Tonfall des Statements"],
                    "suggestions": ["Definiere den gewünschten Tonfall"],
                    "seed_posts": [
                        "SwissBank: 'Die Restrukturierung ist notwendig für die Zukunftsfähigkeit.'",
                        "@FinanzReporter: SwissBank streicht 200 Stellen. Details folgen.",
                        "@BetrofffeneMitarbeiterin: Gerade erfahren. Bin schockiert.",
                    ],
                    "stakeholder_hint": "Mitarbeiter, Kunden, Finanzanalysten, Medien",
                }
            ),
            input_tokens=500,
            output_tokens=400,
            model="mock",
        )

    async def generate_simple(self, prompt, temperature=0.7) -> str:
        return "mock"


@pytest.fixture
def builder():
    return PromptBuilder(MockAnalysisLLM())


class TestPromptBuilder:
    @pytest.mark.asyncio
    async def test_analyze_input_basic(self, builder):
        """Analyze a crisis scenario input."""
        scenario = await builder.analyze_input(
            "SwissBank kündigt Entlassung von 200 Mitarbeitern an. "
            "Statement: Die Restrukturierung ist notwendig."
        )

        assert isinstance(scenario, StructuredScenario)
        assert scenario.industry == "Finanzwesen"
        assert scenario.company == "SwissBank"
        assert scenario.scenario_type == "corporate_crisis"
        assert scenario.controversity_score >= 0.6

    @pytest.mark.asyncio
    async def test_analyze_extracts_seed_posts(self, builder):
        """Seed posts should be generated for simulation injection."""
        scenario = await builder.analyze_input("SwissBank Entlassungen")

        assert len(scenario.seed_posts) >= 2
        assert any("SwissBank" in post for post in scenario.seed_posts)

    @pytest.mark.asyncio
    async def test_analyze_identifies_missing_fields(self, builder):
        """Missing information should be flagged."""
        scenario = await builder.analyze_input("SwissBank Entlassungen")

        assert len(scenario.missing_fields) > 0

    @pytest.mark.asyncio
    async def test_analyze_empty_input(self, builder):
        """Empty/minimal input should return defaults with many missing fields."""
        scenario = await builder.analyze_input("")
        # Even with empty input, should return a valid StructuredScenario
        assert isinstance(scenario, StructuredScenario)

    @pytest.mark.asyncio
    async def test_suggest_improvements(self, builder):
        """Improvement suggestions should be generated."""
        scenario = StructuredScenario(
            industry="Finanzwesen",
            company="SwissBank",
            statement="Entlassungen",
        )

        suggestions = await builder.suggest_improvements(scenario)
        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)

    def test_controversity_level_crisis(self, builder):
        assert builder.get_controversity_level(0.8) == "crisis"

    def test_controversity_level_standard(self, builder):
        assert builder.get_controversity_level(0.5) == "standard"

    def test_controversity_level_routine(self, builder):
        assert builder.get_controversity_level(0.1) == "routine"


class TestStructuredScenario:
    def test_default_values(self):
        scenario = StructuredScenario()
        assert scenario.controversity_score == 0.5
        assert scenario.missing_fields == []
        assert scenario.seed_posts == []

    def test_controversity_clamped(self):
        """Pydantic validates the range — values outside 0-1 raise errors."""
        import pytest as _pytest

        with _pytest.raises(ValueError):
            StructuredScenario(controversity_score=1.5)

    def test_serialization(self):
        scenario = StructuredScenario(
            industry="Tech",
            company="TestCo",
            seed_posts=["Post 1", "Post 2"],
        )
        data = scenario.model_dump()
        assert data["industry"] == "Tech"
        assert len(data["seed_posts"]) == 2

        # Roundtrip
        restored = StructuredScenario.model_validate(data)
        assert restored.company == "TestCo"
