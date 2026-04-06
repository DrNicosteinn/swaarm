"""Tests for Pydantic data models."""

import pytest

from app.models.persona import AgentTier, BigFive, Persona, PostingStyle
from app.models.agent import AgentMemory, AgentState
from app.models.actions import AgentAction, FeedItem, PublicNetworkAction
from app.models.simulation import (
    PlatformType,
    ScenarioControversity,
    SimulationConfig,
    SimulationStatus,
    TierDistribution,
    QualityMetrics,
    RoundMetrics,
)


class TestPersona:
    def test_create_minimal_persona(self):
        persona = Persona(
            id="agent-001",
            name="Claudia Meier",
            age=38,
            gender="female",
            country="CH",
            region="Zürich",
            occupation="Produktmanagerin",
            big_five=BigFive(
                openness=0.7,
                conscientiousness=0.8,
                extraversion=0.4,
                agreeableness=0.6,
                neuroticism=0.3,
            ),
        )
        assert persona.id == "agent-001"
        assert persona.country == "CH"
        assert persona.agent_tier == AgentTier.ACTIVE_RESPONDER
        assert persona.is_zealot is False

    def test_persona_age_validation(self):
        with pytest.raises(ValueError):
            Persona(
                id="test",
                name="Test",
                age=10,  # too young
                gender="male",
                country="DE",
                region="Berlin",
                occupation="Test",
                big_five=BigFive(
                    openness=0.5,
                    conscientiousness=0.5,
                    extraversion=0.5,
                    agreeableness=0.5,
                    neuroticism=0.5,
                ),
            )

    def test_big_five_validation(self):
        with pytest.raises(ValueError):
            BigFive(openness=1.5, conscientiousness=0.5, extraversion=0.5,
                    agreeableness=0.5, neuroticism=0.5)

    def test_zealot_persona(self):
        persona = Persona(
            id="zealot-001",
            name="Max Müller",
            age=55,
            gender="male",
            country="DE",
            region="Bayern",
            occupation="Aktivist",
            big_five=BigFive(
                openness=0.3, conscientiousness=0.6, extraversion=0.9,
                agreeableness=0.2, neuroticism=0.7,
            ),
            is_zealot=True,
            is_contrarian=False,
        )
        assert persona.is_zealot is True


class TestAgentState:
    def test_initial_state(self):
        state = AgentState(persona_id="agent-001")
        assert state.current_sentiment == 0.0
        assert state.posts_created == 0
        assert state.last_active_round == -1
        assert not state.is_on_cooldown(0)

    def test_cooldown(self):
        state = AgentState(persona_id="agent-001")
        state.set_cooldown(current_round=5, cooldown_rounds=3)
        assert state.is_on_cooldown(6)
        assert state.is_on_cooldown(7)
        assert not state.is_on_cooldown(8)
        assert state.last_active_round == 5

    def test_memory_sliding_window(self):
        memory = AgentMemory()
        for i in range(7):
            memory.add_observation(f"Observation {i}")
        assert len(memory.recent_observations) == 5
        assert memory.recent_observations[0] == "Observation 2"

    def test_important_memories_limit(self):
        memory = AgentMemory()
        for i in range(8):
            memory.add_important_memory(f"Important {i}")
        assert len(memory.important_memories) == 5
        assert memory.important_memories[0] == "Important 3"


class TestActions:
    def test_create_post_action(self):
        action = AgentAction(
            agent_id="agent-001",
            round_number=5,
            action_type=PublicNetworkAction.CREATE_POST,
            content="Die neue Regulierung verdient einen genaueren Blick.",
            hashtags=["Regulierung", "FINMA"],
        )
        assert action.content is not None
        assert len(action.hashtags) == 2
        assert not action.is_fallback

    def test_like_action(self):
        action = AgentAction(
            agent_id="agent-002",
            round_number=5,
            action_type=PublicNetworkAction.LIKE,
            target_post_id="post-123",
        )
        assert action.target_post_id == "post-123"
        assert action.content is None

    def test_fallback_action(self):
        action = AgentAction(
            agent_id="agent-003",
            round_number=5,
            action_type=PublicNetworkAction.DO_NOTHING,
            is_fallback=True,
            metadata={"reason": "llm_error"},
        )
        assert action.is_fallback is True

    def test_feed_item(self):
        item = FeedItem(
            post_id="post-001",
            author_id="agent-010",
            author_name="Lisa Hofer",
            content="Employer Branding ist mehr als ein Buzzword.",
            created_round=3,
            likes=12,
            comments=3,
        )
        assert item.likes == 12
        assert item.sentiment == 0.0


class TestSimulationConfig:
    def test_default_config(self):
        config = SimulationConfig(
            simulation_id="sim-001",
            user_id="user-001",
            scenario_text="Test scenario",
        )
        assert config.agent_count == 200
        assert config.round_count == 50
        assert config.platform == PlatformType.PUBLIC

    def test_tier_distribution_crisis(self):
        dist = TierDistribution.for_controversity(ScenarioControversity.CRISIS)
        assert dist.power_creator == 0.10
        assert dist.observer == 0.20
        total = dist.power_creator + dist.active_responder + dist.selective_engager + dist.observer
        assert abs(total - 1.0) < 0.001

    def test_tier_distribution_routine(self):
        dist = TierDistribution.for_controversity(ScenarioControversity.ROUTINE)
        assert dist.observer == 0.70
        total = dist.power_creator + dist.active_responder + dist.selective_engager + dist.observer
        assert abs(total - 1.0) < 0.001

    def test_agent_count_validation(self):
        with pytest.raises(ValueError):
            SimulationConfig(
                simulation_id="test",
                user_id="test",
                scenario_text="Test",
                agent_count=5,  # below minimum
            )

    def test_quality_metrics(self):
        metrics = QualityMetrics(
            sentiment_entropy=0.65,
            engagement_gini=0.72,
            content_uniqueness=0.85,
            quality_badge="green",
        )
        assert metrics.quality_badge == "green"

    def test_round_metrics(self):
        metrics = RoundMetrics(
            round_number=1,
            active_agents=150,
            posts_created=12,
            comments_created=45,
            likes_given=200,
            reposts=8,
            follows=15,
            avg_sentiment=0.2,
        )
        assert metrics.active_agents == 150
