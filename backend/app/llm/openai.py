"""OpenAI LLM provider implementation.

Uses async OpenAI client with function calling, retry logic,
and token usage tracking. Prompt caching is automatic for
prompts with static prefixes >1024 tokens.
"""

import asyncio
import random

from loguru import logger
from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    BadRequestError,
    RateLimitError,
)

from app.llm.base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI API implementation with retry and rate limiting."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
    ):
        self.client = AsyncOpenAI(api_key=api_key, timeout=300.0)
        self.model = model
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def chat(
        self,
        messages: list[dict[str, str]],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> LLMResponse:
        """Send chat completion with retry and error handling."""
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                kwargs: dict = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                }

                # GPT-5.x and o-series models use max_completion_tokens instead of max_tokens
                if self.model.startswith(("gpt-5", "o1", "o3", "o4")):
                    kwargs["max_completion_tokens"] = max_tokens
                else:
                    kwargs["max_tokens"] = max_tokens

                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                response = await self.client.chat.completions.create(**kwargs)

                choice = response.choices[0]
                usage = response.usage

                # Extract tool calls if present
                tool_calls = []
                if choice.message.tool_calls:
                    for tc in choice.message.tool_calls:
                        tool_calls.append(
                            {
                                "id": tc.id,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                        )

                # Extract cached tokens info
                cached = 0
                if usage and hasattr(usage, "prompt_tokens_details"):
                    details = usage.prompt_tokens_details
                    if details and hasattr(details, "cached_tokens"):
                        cached = details.cached_tokens or 0

                return LLMResponse(
                    content=choice.message.content,
                    tool_calls=tool_calls,
                    input_tokens=usage.prompt_tokens if usage else 0,
                    output_tokens=usage.completion_tokens if usage else 0,
                    model=self.model,
                    cached_tokens=cached,
                )

            except RateLimitError as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                # Check for Retry-After header
                retry_after = getattr(e, "retry_after", None)
                if retry_after:
                    delay = float(retry_after)
                logger.warning(f"Rate limited (attempt {attempt + 1}), waiting {delay:.1f}s")
                await asyncio.sleep(delay)

            except (APITimeoutError, APIConnectionError) as e:
                last_error = e
                delay = self._calculate_delay(attempt)
                logger.warning(f"Connection error (attempt {attempt + 1}): {e}, retrying in {delay:.1f}s")
                await asyncio.sleep(delay)

            except BadRequestError as e:
                # Permanent failure — don't retry
                logger.error(f"Bad request (permanent): {e}")
                raise

            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Unexpected error (attempt {attempt + 1}): {e}, retrying in {delay:.1f}s")
                    await asyncio.sleep(delay)

        raise RuntimeError(f"LLM call failed after {self.max_retries} retries: {last_error}") from last_error

    async def generate_simple(self, prompt: str, temperature: float = 0.7) -> str:
        """Simple text generation without tools."""
        response = await self.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=1000,
        )
        return response.content or ""

    def _calculate_delay(self, attempt: int) -> float:
        """Exponential backoff with full jitter."""
        exp_delay = min(self.base_delay * (2**attempt), self.max_delay)
        return random.uniform(0, exp_delay)
