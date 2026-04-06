"""Willingness scoring — determines which agents are active each round.

Uses a Socialtrait-inspired formula combining persona traits and context,
with stochastic Bernoulli activation. Vectorized numpy for 50k+ agents.
"""

import numpy as np
from loguru import logger

from app.models.persona import AgentTier, Persona
from app.models.simulation import ScenarioControversity

# Tier-specific base bonuses and cooldown rounds
TIER_CONFIG = {
    AgentTier.POWER_CREATOR: {"bonus": 0.80, "cooldown": 2},
    AgentTier.ACTIVE_RESPONDER: {"bonus": 0.50, "cooldown": 3},
    AgentTier.SELECTIVE_ENGAGER: {"bonus": 0.20, "cooldown": 5},
    AgentTier.OBSERVER: {"bonus": 0.03, "cooldown": 12},
}


class WillingnessScorer:
    """Computes activation probabilities for all agents each round.

    Uses vectorized numpy operations — <5ms for 50k agents.
    """

    def __init__(
        self,
        personas: list[Persona],
        controversity: ScenarioControversity,
        seed: int | None = None,
    ):
        self.n_agents = len(personas)
        self.rng = np.random.default_rng(seed)

        # Pre-compute static persona scores (never change)
        self.persona_scores = self._compute_persona_scores(personas)

        # Pre-compute tier info
        self.tier_indices = np.array([list(AgentTier).index(p.agent_tier) for p in personas])
        self.cooldowns = np.array([TIER_CONFIG[p.agent_tier]["cooldown"] for p in personas])

        # Controversity affects the overall activation scale
        self.activation_scale = {
            ScenarioControversity.ROUTINE: 0.6,
            ScenarioControversity.STANDARD: 1.0,
            ScenarioControversity.CRISIS: 1.5,
        }[controversity]

        logger.debug(
            f"WillingnessScorer initialized: {self.n_agents} agents, "
            f"controversity={controversity.value}, scale={self.activation_scale}"
        )

    def _compute_persona_scores(self, personas: list[Persona]) -> np.ndarray:
        """Compute static persona willingness scores. Shape: (n_agents,)."""
        scores = np.zeros(self.n_agents)

        for i, p in enumerate(personas):
            # Weighted combination of persona traits
            scores[i] = (
                0.30 * p.big_five.extraversion
                + 0.25 * TIER_CONFIG[p.agent_tier]["bonus"]
                + 0.20 * self._posting_freq_score(p.posting_style.frequency)
                + 0.15 * self._opinion_strength(p.opinions)
                + 0.10 * p.big_five.neuroticism
            )

        return scores

    @staticmethod
    def _posting_freq_score(frequency: str) -> float:
        """Convert posting frequency to a 0-1 score."""
        return {"daily": 0.9, "weekly": 0.5, "monthly": 0.2, "rarely": 0.05}.get(frequency, 0.3)

    @staticmethod
    def _opinion_strength(opinions) -> float:
        """Compute average opinion strength (distance from neutral 0.5)."""
        values = [
            opinions.trust_institutions,
            opinions.environmental_concern,
            opinions.tech_optimism,
            opinions.economic_anxiety,
            opinions.social_progressivism,
        ]
        return np.mean([abs(v - 0.5) * 2 for v in values])  # Scale to 0-1

    def compute_activation(
        self,
        current_round: int,
        last_active_rounds: np.ndarray,
        topic_relevance: np.ndarray | None = None,
        network_activity: np.ndarray | None = None,
        emotional_valence: float = 0.0,
    ) -> np.ndarray:
        """Compute which agents are active this round.

        Args:
            current_round: Current simulation round number
            last_active_rounds: Array of last active round per agent, shape (n,)
            topic_relevance: Per-agent topic relevance scores 0-1, shape (n,)
            network_activity: Per-agent network activity scores 0-1, shape (n,)
            emotional_valence: Global emotional valence of current discourse 0-1

        Returns:
            Boolean mask of active agents, shape (n,)
        """
        n = self.n_agents

        # Default context scores if not provided
        if topic_relevance is None:
            topic_relevance = np.full(n, 0.5)
        if network_activity is None:
            network_activity = np.full(n, 0.3)

        # 1. Context-based willingness (dynamic per round)
        s_context = (
            0.30 * topic_relevance
            + 0.25 * network_activity
            + 0.20 * emotional_valence
            + 0.15 * min(current_round / 10, 1.0)  # Conversation momentum (ramps up)
            + 0.10 * self.rng.random(n)  # Novelty/randomness
        )

        # 2. Unified score (Socialtrait-inspired)
        lambda_ = 1.5
        s_unified = self.persona_scores * np.exp(-lambda_ * (s_context - self.persona_scores))

        # 3. Apply activation scale (controversity)
        s_unified *= self.activation_scale

        # 4. Cooldown mask
        rounds_since_active = current_round - last_active_rounds
        cooldown_factor = np.minimum(rounds_since_active / self.cooldowns, 1.0)
        s_unified *= cooldown_factor

        # 5. Clip to valid probability range
        s_unified = np.clip(s_unified, 0.0, 0.95)

        # 6. Stochastic activation (Bernoulli sampling)
        activated = self.rng.random(n) < s_unified

        return activated

    def get_cooldown_for_agent(self, agent_index: int) -> int:
        """Get the cooldown period for a specific agent (by index)."""
        return int(self.cooldowns[agent_index])
