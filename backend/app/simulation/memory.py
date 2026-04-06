"""Agent memory system — sliding window + importance scoring + periodic summary.

Lightweight design optimized for token efficiency:
- Sliding window: last 3-5 observations (always in prompt)
- Important memories: high-scoring events kept longer (max 5)
- Summary: compressed every 5 rounds to save tokens
"""

from app.llm.base import LLMProvider
from app.models.agent import AgentMemory, AgentState
from app.models.persona import Persona

# Importance threshold: only memories scoring above this are kept
IMPORTANCE_THRESHOLD = 5.0

# How often to compress memories into a summary
SUMMARY_INTERVAL = 5


class MemoryManager:
    """Manages agent memories across simulation rounds."""

    def __init__(self, llm: LLMProvider | None = None):
        self.llm = llm

    def record_observation(
        self,
        state: AgentState,
        observation: str,
        importance: float = 0.0,
    ) -> None:
        """Record what an agent observed or did this round.

        Args:
            state: The agent's current state (mutated in place)
            observation: Text description of what happened
            importance: Score 0-10 (from LLM response or heuristic)
        """
        state.memory.add_observation(observation)

        if importance >= IMPORTANCE_THRESHOLD:
            state.memory.add_important_memory(observation)

    def build_memory_prompt(self, state: AgentState) -> str:
        """Build the memory section of an agent's prompt.

        Token budget: ~150 tokens total.
        """
        parts = []

        # Summary (if available)
        if state.memory.memory_summary:
            parts.append(f"ZUSAMMENFASSUNG: {state.memory.memory_summary}")

        # Important memories
        if state.memory.important_memories:
            parts.append("WICHTIGE ERINNERUNGEN:")
            for mem in state.memory.important_memories[-3:]:  # Max 3 in prompt
                parts.append(f"  - {mem}")

        # Recent observations
        if state.memory.recent_observations:
            parts.append("LETZTE BEOBACHTUNGEN:")
            for obs in state.memory.recent_observations[-3:]:  # Max 3 in prompt
                parts.append(f"  - {obs}")

        if not parts:
            return "Du hast noch keine Erinnerungen."

        return "\n".join(parts)

    async def maybe_summarize(
        self,
        state: AgentState,
        persona: Persona,
        current_round: int,
    ) -> None:
        """Compress memories into a summary every SUMMARY_INTERVAL rounds.

        Only runs if LLM is available and we have enough observations.
        """
        if current_round % SUMMARY_INTERVAL != 0:
            return
        if not self.llm:
            return
        if len(state.memory.recent_observations) < 3:
            return

        # Build summary prompt
        all_memories = []
        if state.memory.memory_summary:
            all_memories.append(f"Bisherige Zusammenfassung: {state.memory.memory_summary}")
        all_memories.extend(state.memory.important_memories)
        all_memories.extend(state.memory.recent_observations)

        memory_text = "\n".join(f"- {m}" for m in all_memories)

        prompt = (
            f"Du bist {persona.name}, {persona.occupation}. "
            f"Fasse deine Erinnerungen in 2-3 kurzen Sätzen zusammen. "
            f"Behalte nur die wichtigsten Punkte.\n\n"
            f"Erinnerungen:\n{memory_text}\n\n"
            f"Zusammenfassung (max 3 Sätze):"
        )

        summary = await self.llm.generate_simple(prompt, temperature=0.3)
        state.memory.memory_summary = summary.strip()[:300]  # Cap at 300 chars

    @staticmethod
    def compute_observation_text(
        action_type: str,
        content: str | None = None,
        target_info: str | None = None,
        engagement: int = 0,
    ) -> str:
        """Create a human-readable observation from an action.

        Used for recording what happened to an agent.
        """
        if action_type == "create_post":
            text = f"Eigenen Post erstellt: \"{content[:80]}\"" if content else "Eigenen Post erstellt"
            if engagement > 0:
                text += f" ({engagement} Reaktionen)"
            return text

        if action_type == "comment":
            return f"Kommentar geschrieben: \"{content[:80]}\"" if content else "Kommentiert"

        if action_type in ("like_post", "react_like", "react_celebrate", "react_insightful"):
            return f"Post von {target_info or 'jemandem'} geliked"

        if action_type == "repost":
            return f"Post von {target_info or 'jemandem'} geteilt"

        if action_type in ("follow_user", "connect"):
            return f"{target_info or 'Jemandem'} gefolgt"

        if action_type == "do_nothing":
            return "Feed beobachtet, nichts getan"

        return f"Aktion: {action_type}"

    @staticmethod
    def compute_importance(
        action_type: str,
        engagement_received: int = 0,
        is_controversial: bool = False,
    ) -> float:
        """Heuristic importance scoring for an action/observation.

        Scale: 0-10. Higher = more likely to be remembered.
        """
        base_scores = {
            "create_post": 4.0,
            "comment": 3.0,
            "like_post": 1.0,
            "repost": 2.0,
            "follow_user": 2.0,
            "do_nothing": 0.0,
        }
        score = base_scores.get(action_type, 2.0)

        # High engagement makes it more memorable
        if engagement_received > 10:
            score += 3.0
        elif engagement_received > 5:
            score += 2.0
        elif engagement_received > 0:
            score += 1.0

        # Controversial content is more memorable
        if is_controversial:
            score += 2.0

        return min(score, 10.0)
