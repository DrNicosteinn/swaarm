"""Agent state models — dynamic state that changes during simulation."""

from pydantic import BaseModel, Field


class AgentMemory(BaseModel):
    """Agent's memory system — sliding window + important memories + summary."""

    recent_observations: list[str] = Field(
        default_factory=list, description="Last 3-5 observations (sliding window)"
    )
    important_memories: list[str] = Field(
        default_factory=list, description="High-importance memories (max 5)"
    )
    memory_summary: str = Field(
        default="", description="Compressed summary of all memories, updated every 5 rounds"
    )

    def add_observation(self, observation: str, max_recent: int = 5) -> None:
        """Add an observation to the sliding window."""
        self.recent_observations.append(observation)
        if len(self.recent_observations) > max_recent:
            self.recent_observations.pop(0)

    def add_important_memory(self, memory: str, max_important: int = 5) -> None:
        """Add a high-importance memory."""
        self.important_memories.append(memory)
        if len(self.important_memories) > max_important:
            self.important_memories.pop(0)


class AgentState(BaseModel):
    """Dynamic state of an agent during simulation. Changes every round."""

    persona_id: str

    # Memory
    memory: AgentMemory = Field(default_factory=AgentMemory)

    # Current state
    current_sentiment: float = Field(
        default=0.0, ge=-1.0, le=1.0, description="Current sentiment -1.0 to 1.0"
    )
    opinion_shifts: dict[str, float] = Field(
        default_factory=dict, description="Opinion changes since simulation start"
    )

    # Activity tracking
    posts_created: int = 0
    comments_created: int = 0
    likes_given: int = 0
    total_engagement_received: int = 0
    last_active_round: int = -1
    cooldown_until: int = 0  # Round number until agent can act again

    def is_on_cooldown(self, current_round: int) -> bool:
        """Check if agent is still in cooldown period."""
        return current_round < self.cooldown_until

    def set_cooldown(self, current_round: int, cooldown_rounds: int) -> None:
        """Set cooldown after agent takes an action."""
        self.cooldown_until = current_round + cooldown_rounds
        self.last_active_round = current_round
