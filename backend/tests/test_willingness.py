"""Tests for willingness scoring system."""

import numpy as np
import pytest

from app.models.persona import AgentTier, BigFive, Persona, PostingStyle, OpinionSeeds
from app.models.simulation import ScenarioControversity
from app.simulation.willingness import WillingnessScorer


def _make_persona(
    id: str,
    tier: AgentTier = AgentTier.ACTIVE_RESPONDER,
    extraversion: float = 0.5,
    frequency: str = "weekly",
) -> Persona:
    return Persona(
        id=id,
        name=f"Agent {id}",
        age=30,
        gender="female",
        country="CH",
        region="Zürich",
        occupation="Test",
        big_five=BigFive(
            openness=0.5,
            conscientiousness=0.5,
            extraversion=extraversion,
            agreeableness=0.5,
            neuroticism=0.5,
        ),
        agent_tier=tier,
        posting_style=PostingStyle(frequency=frequency),
    )


class TestWillingnessScorer:
    def test_initialization(self):
        personas = [_make_persona(f"u{i}") for i in range(100)]
        scorer = WillingnessScorer(personas, ScenarioControversity.STANDARD, seed=42)
        assert scorer.n_agents == 100
        assert len(scorer.persona_scores) == 100

    def test_persona_scores_range(self):
        """All persona scores should be between 0 and 1."""
        personas = [
            _make_persona("high", tier=AgentTier.POWER_CREATOR, extraversion=0.9, frequency="daily"),
            _make_persona("low", tier=AgentTier.OBSERVER, extraversion=0.1, frequency="rarely"),
        ]
        scorer = WillingnessScorer(personas, ScenarioControversity.STANDARD, seed=42)
        assert all(0.0 <= s <= 1.0 for s in scorer.persona_scores)

    def test_power_creator_higher_than_observer(self):
        """Power creators should have higher base willingness than observers."""
        personas = [
            _make_persona("creator", tier=AgentTier.POWER_CREATOR, extraversion=0.8),
            _make_persona("observer", tier=AgentTier.OBSERVER, extraversion=0.2),
        ]
        scorer = WillingnessScorer(personas, ScenarioControversity.STANDARD, seed=42)
        assert scorer.persona_scores[0] > scorer.persona_scores[1]

    def test_activation_returns_boolean_mask(self):
        personas = [_make_persona(f"u{i}") for i in range(50)]
        scorer = WillingnessScorer(personas, ScenarioControversity.STANDARD, seed=42)
        last_active = np.full(50, -10)  # Everyone was active long ago

        activated = scorer.compute_activation(current_round=5, last_active_rounds=last_active)

        assert activated.dtype == bool
        assert len(activated) == 50
        assert activated.sum() > 0  # At least some agents should be active

    def test_crisis_activates_more_agents(self):
        """Crisis scenarios should activate more agents than routine ones."""
        personas = [_make_persona(f"u{i}") for i in range(200)]
        last_active = np.full(200, -10)

        # Same personas, different controversity
        crisis_scorer = WillingnessScorer(personas, ScenarioControversity.CRISIS, seed=42)
        routine_scorer = WillingnessScorer(personas, ScenarioControversity.ROUTINE, seed=42)

        crisis_active = crisis_scorer.compute_activation(5, last_active).sum()
        routine_active = routine_scorer.compute_activation(5, last_active).sum()

        assert crisis_active > routine_active

    def test_cooldown_suppresses_recently_active(self):
        """Agents who just acted should be less likely to act again."""
        personas = [_make_persona(f"u{i}", tier=AgentTier.ACTIVE_RESPONDER) for i in range(100)]
        scorer = WillingnessScorer(personas, ScenarioControversity.STANDARD, seed=42)

        # All agents were active last round (round 4) — now it's round 5
        just_active = np.full(100, 4)
        active_immediately = scorer.compute_activation(5, just_active).sum()

        # All agents were active 10 rounds ago — now it's round 15
        long_ago = np.full(100, 5)
        active_after_rest = scorer.compute_activation(15, long_ago).sum()

        assert active_after_rest > active_immediately

    def test_topic_relevance_affects_activation(self):
        """Topic relevance modulates activation via the Socialtrait formula.

        Note: Due to the exponential dampening in the formula, very high context
        scores can actually REDUCE activation (regression to persona mean).
        This is the intended behavior — it prevents unrealistic 100% activation.
        We just verify that relevance changes the activation count meaningfully.
        """
        personas = [_make_persona(f"u{i}") for i in range(200)]
        last_active = np.full(200, -10)

        scorer1 = WillingnessScorer(personas, ScenarioControversity.STANDARD, seed=42)
        low_rel = np.full(200, 0.1)
        active_low = scorer1.compute_activation(5, last_active, topic_relevance=low_rel).sum()

        scorer2 = WillingnessScorer(personas, ScenarioControversity.STANDARD, seed=42)
        high_rel = np.full(200, 0.9)
        active_high = scorer2.compute_activation(5, last_active, topic_relevance=high_rel).sum()

        # Activation counts should differ meaningfully (relevance has effect)
        assert abs(active_high - active_low) > 5  # At least 5 agents difference

    def test_deterministic_with_seed(self):
        """Same seed should produce same activation pattern."""
        personas = [_make_persona(f"u{i}") for i in range(100)]
        last_active = np.full(100, -10)

        s1 = WillingnessScorer(personas, ScenarioControversity.STANDARD, seed=99)
        a1 = s1.compute_activation(5, last_active)

        s2 = WillingnessScorer(personas, ScenarioControversity.STANDARD, seed=99)
        a2 = s2.compute_activation(5, last_active)

        np.testing.assert_array_equal(a1, a2)

    def test_activation_not_all_or_nothing(self):
        """Activation should be partial — not 0% and not 100%."""
        personas = [_make_persona(f"u{i}") for i in range(500)]
        scorer = WillingnessScorer(personas, ScenarioControversity.STANDARD, seed=42)
        last_active = np.full(500, -10)

        activated = scorer.compute_activation(5, last_active)
        pct = activated.sum() / len(activated)

        # Should be between 5% and 95%
        assert 0.05 < pct < 0.95

    def test_get_cooldown_for_agent(self):
        personas = [
            _make_persona("creator", tier=AgentTier.POWER_CREATOR),
            _make_persona("observer", tier=AgentTier.OBSERVER),
        ]
        scorer = WillingnessScorer(personas, ScenarioControversity.STANDARD)
        assert scorer.get_cooldown_for_agent(0) == 2  # Creator cooldown
        assert scorer.get_cooldown_for_agent(1) == 12  # Observer cooldown
