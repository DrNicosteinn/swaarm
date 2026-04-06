"""Abstract platform interface.

Every simulated platform (public/professional) must implement this interface.
This ensures the simulation engine is platform-agnostic.
"""

from abc import ABC, abstractmethod

from app.models.actions import AgentAction, FeedItem
from app.models.persona import Persona
from app.simulation.database import SimulationDB
from app.simulation.graph import SocialGraph


class PlatformBase(ABC):
    """Base class for simulated social media platforms."""

    def __init__(self, db: SimulationDB, graph: SocialGraph):
        self.db = db
        self.graph = graph

    @abstractmethod
    def get_platform_name(self) -> str:
        """Return the display name of this platform."""
        ...

    @abstractmethod
    def get_action_types(self) -> list[str]:
        """Return available action types for this platform."""
        ...

    @abstractmethod
    def get_tools_schema(self) -> list[dict]:
        """Return OpenAI function calling tool definitions for agent actions."""
        ...

    @abstractmethod
    async def generate_feed(
        self,
        agent_id: str,
        agent_persona: Persona,
        current_round: int,
        feed_size: int = 5,
    ) -> list[FeedItem]:
        """Generate a personalized feed for an agent."""
        ...

    @abstractmethod
    def format_feed_for_prompt(self, feed: list[FeedItem], current_round: int) -> str:
        """Serialize a feed into compact text for the LLM prompt."""
        ...

    @abstractmethod
    async def execute_action(self, action: AgentAction) -> bool:
        """Execute an agent action against the database. Returns True if successful."""
        ...

    @abstractmethod
    def get_platform_rules_prompt(self) -> str:
        """Return platform-specific rules for the system prompt."""
        ...
