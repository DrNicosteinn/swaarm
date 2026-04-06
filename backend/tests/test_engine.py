"""Tests for the simulation engine — uses a mock LLM, no real API calls."""

import json
import os
import tempfile

import pytest

from app.llm.base import LLMProvider, LLMResponse
from app.models.persona import AgentTier, BigFive, Persona
from app.models.simulation import PlatformType, ScenarioControversity, SimulationConfig, SimulationStatus
from app.simulation.database import SimulationDB
from app.simulation.engine import SimulationEngine
from app.simulation.graph import SocialGraph
from app.simulation.platforms.public import PublicNetworkPlatform


class MockLLMProvider(LLMProvider):
    """Mock LLM that returns deterministic tool calls for testing."""

    def __init__(self):
        self.call_count = 0

    async def chat(self, messages, tools=None, temperature=0.7, max_tokens=500) -> LLMResponse:
        self.call_count += 1

        # Alternate between different actions for variety
        if self.call_count % 4 == 1:
            # Create a post
            return LLMResponse(
                tool_calls=[
                    {
                        "id": f"call_{self.call_count}",
                        "function": {
                            "name": "create_post",
                            "arguments": json.dumps(
                                {
                                    "content": f"Testpost Nummer {self.call_count}",
                                    "hashtags": ["test"],
                                }
                            ),
                        },
                    }
                ],
                input_tokens=500,
                output_tokens=50,
                model="mock-model",
            )
        elif self.call_count % 4 == 2:
            # Like a post
            return LLMResponse(
                tool_calls=[
                    {
                        "id": f"call_{self.call_count}",
                        "function": {
                            "name": "like_post",
                            "arguments": json.dumps({"post_id": "p-initial"}),
                        },
                    }
                ],
                input_tokens=500,
                output_tokens=30,
                model="mock-model",
            )
        elif self.call_count % 4 == 3:
            # Comment
            return LLMResponse(
                tool_calls=[
                    {
                        "id": f"call_{self.call_count}",
                        "function": {
                            "name": "comment",
                            "arguments": json.dumps(
                                {
                                    "post_id": "p-initial",
                                    "content": "Interessanter Punkt!",
                                }
                            ),
                        },
                    }
                ],
                input_tokens=500,
                output_tokens=40,
                model="mock-model",
            )
        else:
            # Do nothing
            return LLMResponse(
                tool_calls=[
                    {
                        "id": f"call_{self.call_count}",
                        "function": {
                            "name": "do_nothing",
                            "arguments": "{}",
                        },
                    }
                ],
                input_tokens=300,
                output_tokens=20,
                model="mock-model",
            )

    async def generate_simple(self, prompt, temperature=0.7) -> str:
        return "Zusammenfassung der bisherigen Diskussion."


def _make_persona(id: str, tier: AgentTier = AgentTier.ACTIVE_RESPONDER) -> Persona:
    return Persona(
        id=id,
        name=f"Agent {id}",
        age=30,
        gender="female",
        country="CH",
        region="Zürich",
        occupation="Testperson",
        big_five=BigFive(
            openness=0.5,
            conscientiousness=0.5,
            extraversion=0.6,
            agreeableness=0.5,
            neuroticism=0.4,
        ),
        agent_tier=tier,
        stakeholder_role="general",
        interests=["test"],
    )


@pytest.fixture
async def engine_setup():
    """Set up a complete simulation engine with mock LLM."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    # Create personas — mix of tiers
    personas = (
        [_make_persona(f"creator-{i}", AgentTier.POWER_CREATOR) for i in range(2)]
        + [_make_persona(f"responder-{i}", AgentTier.ACTIVE_RESPONDER) for i in range(5)]
        + [_make_persona(f"engager-{i}", AgentTier.SELECTIVE_ENGAGER) for i in range(3)]
        + [_make_persona(f"observer-{i}", AgentTier.OBSERVER) for i in range(5)]
    )

    config = SimulationConfig(
        simulation_id="test-sim-001",
        user_id="test-user",
        scenario_text="Test scenario",
        agent_count=len(personas),
        round_count=5,
        controversity=ScenarioControversity.STANDARD,
        max_concurrent_llm_calls=5,
        seed=42,
    )

    db = SimulationDB(db_path)
    await db.initialize()

    graph = SocialGraph(PlatformType.PUBLIC)
    graph.initialize(personas, seed=42)

    platform = PublicNetworkPlatform(db, graph)
    llm = MockLLMProvider()

    # Insert users into DB
    users = [(p.id, p.name, "{}", "{}") for p in personas]
    await db.insert_users_batch(users)

    # Insert an initial post so agents have something to react to
    await db.insert_post("p-initial", "creator-0", "Dies ist der initiale Testpost.", created_round=0)

    engine = SimulationEngine(
        config=config,
        db=db,
        graph=graph,
        platform=platform,
        llm=llm,
        personas=personas,
    )

    yield engine, db, llm

    os.unlink(db_path)


class TestSimulationEngine:
    @pytest.mark.asyncio
    async def test_simulation_completes(self, engine_setup):
        """A mini simulation runs to completion."""
        engine, _db, _llm = engine_setup
        result = await engine.run()

        assert result.status == SimulationStatus.COMPLETED
        assert result.completed_rounds == 5
        assert result.completion_percentage == 100.0
        assert result.is_usable is True

    @pytest.mark.asyncio
    async def test_simulation_produces_actions(self, engine_setup):
        """Simulation produces posts, likes, and comments."""
        engine, db, _llm = engine_setup
        await engine.run()

        total_posts = await db.get_total_post_count()
        assert total_posts > 1  # At least the initial + some new ones

    @pytest.mark.asyncio
    async def test_simulation_tracks_costs(self, engine_setup):
        """LLM usage is tracked."""
        engine, _db, _llm = engine_setup
        await engine.run()

        assert engine.usage.total_calls > 0
        assert engine.usage.total_input_tokens > 0
        assert engine.usage.total_output_tokens > 0

    @pytest.mark.asyncio
    async def test_round_metrics_collected(self, engine_setup):
        """Metrics are collected for each round."""
        engine, _db, _llm = engine_setup
        result = await engine.run()

        assert len(result.round_metrics) == 5
        for metrics in result.round_metrics:
            assert metrics.round_number >= 1
            assert metrics.active_agents >= 0

    @pytest.mark.asyncio
    async def test_agent_states_updated(self, engine_setup):
        """Agent states are updated after actions."""
        engine, _db, _llm = engine_setup
        await engine.run()

        # At least some agents should have recorded activity
        active_agents = [s for s in engine.agent_states.values() if s.last_active_round >= 0]
        assert len(active_agents) > 0

    @pytest.mark.asyncio
    async def test_event_callback(self, engine_setup):
        """Events are emitted during simulation."""
        engine, _db, _llm = engine_setup

        events = []

        async def capture_event(event):
            events.append(event)

        engine.event_callback = capture_event
        await engine.run()

        # Should have at least round_complete events + simulation_complete
        assert len(events) >= 6  # 5 rounds + 1 sim complete
        assert events[-1].event_type == "simulation_complete"

    @pytest.mark.asyncio
    async def test_memory_recorded(self, engine_setup):
        """Agent memories are recorded after actions."""
        engine, _db, _llm = engine_setup
        await engine.run()

        # Check that at least one agent has memories
        has_memory = any(len(s.memory.recent_observations) > 0 for s in engine.agent_states.values())
        assert has_memory
