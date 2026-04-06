"""Simulation resilience — circuit breaker, health monitoring, budget safety.

Ensures simulations degrade gracefully instead of crashing completely.
"""

from enum import StrEnum

from loguru import logger
from pydantic import BaseModel, Field


class SimulationAction(StrEnum):
    """What the engine should do in response to errors."""

    CONTINUE = "continue"
    SLOW_DOWN = "slow_down"
    PAUSE = "pause"
    STOP = "stop"


class HealthMonitor(BaseModel):
    """Monitors simulation health and triggers circuit breaker actions.

    Tracks failures per round and cumulative, with configurable thresholds.
    """

    total_agents: int
    failure_threshold: float = 0.15  # 15% failures → pause
    consecutive_error_limit: int = 50  # 50 consecutive errors → slow down
    budget_limit_usd: float | None = None

    # State
    failed_agents: set[str] = Field(default_factory=set)
    round_failures: int = 0
    consecutive_errors: int = 0
    total_errors: int = 0
    current_cost_usd: float = 0.0

    model_config = {"arbitrary_types_allowed": True}

    def record_success(self) -> None:
        """Record a successful agent processing."""
        self.consecutive_errors = 0

    def record_failure(self, agent_id: str, error: str) -> SimulationAction:
        """Record an agent failure and determine what to do.

        Returns the recommended action for the simulation engine.
        """
        self.failed_agents.add(agent_id)
        self.round_failures += 1
        self.total_errors += 1
        self.consecutive_errors += 1

        failure_rate = len(self.failed_agents) / max(self.total_agents, 1)

        if failure_rate > self.failure_threshold:
            logger.error(
                f"Circuit breaker: {failure_rate:.1%} agents failed "
                f"({len(self.failed_agents)}/{self.total_agents}). Pausing."
            )
            return SimulationAction.PAUSE

        if self.consecutive_errors > self.consecutive_error_limit:
            logger.warning(f"Consecutive errors: {self.consecutive_errors}. Slowing down.")
            return SimulationAction.SLOW_DOWN

        return SimulationAction.CONTINUE

    def record_cost(self, cost_usd: float) -> SimulationAction:
        """Record cost and check budget."""
        self.current_cost_usd += cost_usd

        if self.budget_limit_usd and self.current_cost_usd > self.budget_limit_usd:
            logger.error(
                f"Budget exceeded: ${self.current_cost_usd:.4f} > ${self.budget_limit_usd:.4f}. Stopping."
            )
            return SimulationAction.STOP

        return SimulationAction.CONTINUE

    def reset_round(self) -> None:
        """Reset per-round counters at the start of each round."""
        self.round_failures = 0

    def get_status(self) -> dict:
        """Return current health status."""
        return {
            "total_errors": self.total_errors,
            "failed_agents": len(self.failed_agents),
            "failure_rate": len(self.failed_agents) / max(self.total_agents, 1),
            "consecutive_errors": self.consecutive_errors,
            "current_cost_usd": round(self.current_cost_usd, 4),
            "budget_remaining_usd": (
                round(self.budget_limit_usd - self.current_cost_usd, 4) if self.budget_limit_usd else None
            ),
        }
