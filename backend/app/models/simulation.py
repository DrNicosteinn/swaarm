"""Simulation configuration and result models."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PlatformType(StrEnum):
    """Available simulated platforms."""

    PUBLIC = "public"  # Twitter-like
    PROFESSIONAL = "professional"  # LinkedIn-like


class SimulationStatus(StrEnum):
    """Lifecycle status of a simulation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ScenarioControversity(StrEnum):
    """How controversial the scenario is — drives agent activity distribution."""

    ROUTINE = "routine"  # 30% active
    STANDARD = "standard"  # 50% active
    CRISIS = "crisis"  # 80%+ active


class TierDistribution(BaseModel):
    """Distribution of agent tiers based on scenario controversity."""

    power_creator: float = 0.05
    active_responder: float = 0.25
    selective_engager: float = 0.20
    observer: float = 0.50

    @classmethod
    def for_controversity(cls, level: ScenarioControversity) -> "TierDistribution":
        """Get tier distribution for a given controversity level."""
        distributions = {
            ScenarioControversity.ROUTINE: cls(
                power_creator=0.03,
                active_responder=0.12,
                selective_engager=0.15,
                observer=0.70,
            ),
            ScenarioControversity.STANDARD: cls(
                power_creator=0.05,
                active_responder=0.25,
                selective_engager=0.20,
                observer=0.50,
            ),
            ScenarioControversity.CRISIS: cls(
                power_creator=0.10,
                active_responder=0.40,
                selective_engager=0.30,
                observer=0.20,
            ),
        }
        return distributions[level]


class SimulationConfig(BaseModel):
    """Configuration for a simulation run."""

    # Core
    simulation_id: str
    user_id: str

    # Scenario
    scenario_text: str
    scenario_structured: dict[str, Any] = Field(default_factory=dict)
    platform: PlatformType = PlatformType.PUBLIC
    controversity: ScenarioControversity = ScenarioControversity.STANDARD

    # Parameters
    agent_count: int = Field(default=200, ge=10, le=100000)
    round_count: int = Field(default=50, ge=5, le=200)
    base_persona_count: int = Field(default=500, ge=50, le=1000)

    # LLM
    llm_model: str = "gpt-4o-mini"
    max_concurrent_llm_calls: int = 30
    budget_limit_usd: float | None = None

    # Advanced
    tier_distribution: TierDistribution = Field(default_factory=TierDistribution)
    seed: int | None = None  # For reproducible simulations


class RoundMetrics(BaseModel):
    """Metrics collected after each simulation round."""

    round_number: int
    active_agents: int
    posts_created: int
    comments_created: int
    likes_given: int
    reposts: int
    follows: int
    avg_sentiment: float = 0.0
    sentiment_distribution: dict[str, int] = Field(default_factory=dict)  # positive/neutral/negative
    llm_calls: int = 0
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    error_count: int = 0


class SimulationEvent(BaseModel):
    """An event emitted during simulation for live-streaming."""

    round: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str  # post_created, post_liked, user_followed, round_complete, etc.
    data: dict[str, Any] = Field(default_factory=dict)


class QualityMetrics(BaseModel):
    """Quality assurance metrics for a completed simulation."""

    sentiment_entropy: float = 0.0  # Shannon entropy, target 0.5-0.8
    engagement_gini: float = 0.0  # Gini coefficient, target 0.5-0.8
    content_uniqueness: float = 0.0  # Unique trigram ratio, target >0.6
    persona_consistency: float = 0.0  # Average consistency score, target >0.7
    clustering_coefficient: float = 0.0  # Network clustering, target 0.1-0.5
    quality_badge: str = "green"  # green, yellow, red


class SimulationResult(BaseModel):
    """Complete result of a simulation run."""

    simulation_id: str
    status: SimulationStatus
    config: SimulationConfig
    completed_rounds: int = 0
    total_rounds: int = 0
    completion_percentage: float = 0.0
    round_metrics: list[RoundMetrics] = Field(default_factory=list)
    quality: QualityMetrics = Field(default_factory=QualityMetrics)
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    duration_seconds: float = 0.0
    failure_reason: str | None = None
    is_usable: bool = True  # True if at least 60% complete
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
