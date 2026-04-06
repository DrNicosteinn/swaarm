"""Abstract LLM interface — provider-agnostic.

Every LLM provider (OpenAI, Anthropic, Gemini, etc.) must implement this interface.
This ensures the simulation engine is never tied to a single provider.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""

    content: str | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    cached_tokens: int = 0  # How many input tokens were cached


class LLMUsageTracker(BaseModel):
    """Tracks cumulative LLM usage across a simulation."""

    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cached_tokens: int = 0
    total_errors: int = 0
    model: str = ""

    @property
    def total_cost_usd(self) -> float:
        """Estimate total cost based on model pricing."""
        pricing = {
            "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000, "cached": 0.075 / 1_000_000},
            "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000, "cached": 1.25 / 1_000_000},
        }
        rates = pricing.get(self.model, pricing["gpt-4o-mini"])
        uncached_input = self.total_input_tokens - self.total_cached_tokens
        return (
            uncached_input * rates["input"]
            + self.total_cached_tokens * rates["cached"]
            + self.total_output_tokens * rates["output"]
        )

    def record(self, response: LLMResponse) -> None:
        """Record usage from an LLM response."""
        self.total_calls += 1
        self.total_input_tokens += response.input_tokens
        self.total_output_tokens += response.output_tokens
        self.total_cached_tokens += response.cached_tokens
        if not self.model:
            self.model = response.model

    def record_error(self) -> None:
        """Record a failed LLM call."""
        self.total_errors += 1


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> LLMResponse:
        """Send a chat completion request.

        Args:
            messages: List of {"role": "system"|"user"|"assistant", "content": "..."}
            tools: Optional list of function calling tool definitions
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum output tokens

        Returns:
            Standardized LLMResponse
        """
        ...

    @abstractmethod
    async def generate_simple(self, prompt: str, temperature: float = 0.7) -> str:
        """Simple text generation without tools. Returns raw text."""
        ...
