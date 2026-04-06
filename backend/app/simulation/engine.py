"""Simulation engine — the core loop that runs a multi-agent simulation.

Orchestrates: activation → feed → LLM decisions → actions → metrics → events.
Handles tiered agent processing, error recovery, and event emission.
"""

import asyncio
import json
import time
from collections.abc import Callable, Coroutine
from typing import Any

import numpy as np
from loguru import logger

from app.llm.base import LLMProvider, LLMUsageTracker
from app.models.actions import AgentAction
from app.models.agent import AgentState
from app.models.persona import AgentTier, Persona
from app.models.simulation import (
    RoundMetrics,
    SimulationConfig,
    SimulationEvent,
    SimulationResult,
    SimulationStatus,
)
from app.simulation.database import SimulationDB
from app.simulation.graph import SocialGraph
from app.simulation.memory import MemoryManager
from app.simulation.platforms.base import PlatformBase
from app.simulation.willingness import WillingnessScorer

# Type alias for the event callback
EventCallback = Callable[[SimulationEvent], Coroutine[Any, Any, None]]


class SimulationEngine:
    """Runs a complete multi-agent social simulation."""

    def __init__(
        self,
        config: SimulationConfig,
        db: SimulationDB,
        graph: SocialGraph,
        platform: PlatformBase,
        llm: LLMProvider,
        personas: list[Persona],
        event_callback: EventCallback | None = None,
    ):
        self.config = config
        self.db = db
        self.graph = graph
        self.platform = platform
        self.llm = llm
        self.personas = personas
        self.event_callback = event_callback

        # Build persona lookup
        self.persona_map: dict[str, Persona] = {p.id: p for p in personas}

        # Initialize agent states
        self.agent_states: dict[str, AgentState] = {
            p.id: AgentState(persona_id=p.id) for p in personas
        }

        # Initialize subsystems
        self.scorer = WillingnessScorer(personas, config.controversity, seed=config.seed)
        self.memory = MemoryManager(llm=llm)
        self.usage = LLMUsageTracker(model=config.llm_model)

        # Concurrency control
        self.semaphore = asyncio.Semaphore(config.max_concurrent_llm_calls)

        # Track last active rounds for willingness scoring
        self.last_active_rounds = np.full(len(personas), -10, dtype=np.int32)

        # Round metrics history
        self.round_metrics: list[RoundMetrics] = []

    async def run(self) -> SimulationResult:
        """Run the complete simulation. Returns results even on partial failure."""
        start_time = time.monotonic()
        completed_rounds = 0
        failure_reason = None

        logger.info(
            f"Simulation {self.config.simulation_id} starting: "
            f"{len(self.personas)} agents, {self.config.round_count} rounds"
        )

        try:
            for round_num in range(1, self.config.round_count + 1):
                round_metrics = await self._run_round(round_num)
                self.round_metrics.append(round_metrics)
                completed_rounds = round_num

                # Save metrics to DB
                await self.db.save_round_metrics(round_num, round_metrics.model_dump_json())

                # Emit round complete event
                await self._emit_event(SimulationEvent(
                    round=round_num,
                    event_type="round_complete",
                    data={
                        "active_agents": round_metrics.active_agents,
                        "posts_created": round_metrics.posts_created,
                        "avg_sentiment": round_metrics.avg_sentiment,
                        "cost_usd": round_metrics.cost_usd,
                    },
                ))

                logger.info(
                    f"Round {round_num}/{self.config.round_count}: "
                    f"{round_metrics.active_agents} active, "
                    f"{round_metrics.posts_created} posts, "
                    f"${round_metrics.cost_usd:.4f}"
                )

        except Exception as e:
            failure_reason = str(e)
            logger.error(f"Simulation failed at round {completed_rounds + 1}: {e}")

        elapsed = time.monotonic() - start_time

        # Determine status
        if failure_reason:
            status = SimulationStatus.FAILED
        elif completed_rounds == self.config.round_count:
            status = SimulationStatus.COMPLETED
        else:
            status = SimulationStatus.PAUSED

        result = SimulationResult(
            simulation_id=self.config.simulation_id,
            status=status,
            config=self.config,
            completed_rounds=completed_rounds,
            total_rounds=self.config.round_count,
            completion_percentage=round(completed_rounds / self.config.round_count * 100, 1),
            round_metrics=self.round_metrics,
            total_cost_usd=self.usage.total_cost_usd,
            total_tokens=self.usage.total_input_tokens + self.usage.total_output_tokens,
            duration_seconds=elapsed,
            failure_reason=failure_reason,
            is_usable=completed_rounds >= self.config.round_count * 0.6,
        )

        # Emit simulation complete event
        await self._emit_event(SimulationEvent(
            round=completed_rounds,
            event_type="simulation_complete",
            data={
                "status": status.value,
                "completed_rounds": completed_rounds,
                "total_cost_usd": result.total_cost_usd,
                "duration_seconds": elapsed,
            },
        ))

        logger.info(
            f"Simulation {self.config.simulation_id} {status.value}: "
            f"{completed_rounds}/{self.config.round_count} rounds, "
            f"${result.total_cost_usd:.4f}, {elapsed:.1f}s"
        )

        return result

    async def _run_round(self, round_num: int) -> RoundMetrics:
        """Execute a single simulation round."""
        round_start = time.monotonic()
        round_tokens = 0
        round_errors = 0
        actions_this_round: list[AgentAction] = []

        # Phase 1: ACTIVATION (~5ms for 50k agents)
        activated_mask = self.scorer.compute_activation(
            current_round=round_num,
            last_active_rounds=self.last_active_rounds,
        )
        active_indices = np.where(activated_mask)[0]
        active_personas = [self.personas[i] for i in active_indices]

        # Phase 2 & 3: FEED + LLM DECISIONS (async, parallel)
        tasks = []
        for idx, persona in zip(active_indices, active_personas, strict=False):
            tier = persona.agent_tier

            if tier in (AgentTier.POWER_CREATOR, AgentTier.ACTIVE_RESPONDER):
                # Full LLM call
                tasks.append(self._process_agent_full(persona, round_num, int(idx)))
            elif tier == AgentTier.SELECTIVE_ENGAGER:
                # Simplified LLM call
                tasks.append(self._process_agent_simplified(persona, round_num, int(idx)))
            else:
                # Observer: rule-based, no LLM
                tasks.append(self._process_agent_observer(persona, round_num, int(idx)))

        # Execute all agent tasks concurrently (batched via semaphore)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Phase 4: PROCESS RESULTS
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                round_errors += 1
                logger.warning(f"Agent {active_personas[i].id} failed: {result}")
                # Degrade to observer action
                action = AgentAction(
                    agent_id=active_personas[i].id,
                    round_number=round_num,
                    action_type="do_nothing",
                    is_fallback=True,
                    metadata={"error": str(result)[:200]},
                )
            elif result is None:
                continue
            else:
                action = result

            actions_this_round.append(action)

            # Execute action on platform
            try:
                await self.platform.execute_action(action)
            except Exception as e:
                logger.warning(f"Action execution failed for {action.agent_id}: {e}")
                round_errors += 1

            # Update agent state
            idx = active_indices[i]
            state = self.agent_states[action.agent_id]
            cooldown = self.scorer.get_cooldown_for_agent(int(idx))
            state.set_cooldown(round_num, cooldown)
            self.last_active_rounds[idx] = round_num

            # Record memory
            obs_text = MemoryManager.compute_observation_text(
                action.action_type,
                content=action.content,
                target_info=action.target_user_id or action.target_post_id,
            )
            importance = MemoryManager.compute_importance(action.action_type)
            self.memory.record_observation(state, obs_text, importance)

            # Track stats
            if action.action_type == "create_post":
                state.posts_created += 1
            elif action.action_type == "comment":
                state.comments_created += 1
            elif action.action_type in ("like_post", "react_like"):
                state.likes_given += 1

        # Phase 5: METRICS
        posts_created = sum(1 for a in actions_this_round if a.action_type == "create_post")
        comments_created = sum(1 for a in actions_this_round if a.action_type == "comment")
        likes_given = sum(1 for a in actions_this_round if a.action_type in ("like_post", "react_like"))
        reposts = sum(1 for a in actions_this_round if a.action_type == "repost")
        follows = sum(1 for a in actions_this_round if a.action_type in ("follow_user", "connect"))

        round_duration = time.monotonic() - round_start

        return RoundMetrics(
            round_number=round_num,
            active_agents=len(active_indices),
            posts_created=posts_created,
            comments_created=comments_created,
            likes_given=likes_given,
            reposts=reposts,
            follows=follows,
            llm_calls=self.usage.total_calls - sum(m.llm_calls for m in self.round_metrics),
            tokens_used=round_tokens,
            cost_usd=round(round_duration * 0, 4),  # Will be calculated from usage tracker
            duration_seconds=round(round_duration, 3),
            error_count=round_errors,
        )

    async def _process_agent_full(
        self, persona: Persona, round_num: int, agent_index: int
    ) -> AgentAction | None:
        """Full LLM processing for power creators and active responders."""
        async with self.semaphore:
            # Generate feed
            feed = await self.platform.generate_feed(
                persona.id, persona, round_num, feed_size=5
            )

            if not feed and round_num > 1:
                # No feed available — do nothing
                return AgentAction(
                    agent_id=persona.id,
                    round_number=round_num,
                    action_type="do_nothing",
                )

            # Build prompt
            state = self.agent_states[persona.id]
            memory_text = self.memory.build_memory_prompt(state)
            feed_text = self.platform.format_feed_for_prompt(feed, round_num)
            system_prompt = self._build_system_prompt(persona)
            user_prompt = self._build_user_prompt(persona, memory_text, feed_text, round_num)

            # Call LLM
            response = await self.llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                tools=self.platform.get_tools_schema(),
                temperature=0.7 if persona.agent_tier == AgentTier.POWER_CREATOR else 0.5,
                max_tokens=300,
            )
            self.usage.record(response)

            # Parse action from tool calls
            return self._parse_llm_response(response, persona.id, round_num, feed)

    async def _process_agent_simplified(
        self, persona: Persona, round_num: int, agent_index: int
    ) -> AgentAction | None:
        """Simplified LLM processing for selective engagers."""
        async with self.semaphore:
            feed = await self.platform.generate_feed(
                persona.id, persona, round_num, feed_size=3
            )

            if not feed:
                return AgentAction(
                    agent_id=persona.id,
                    round_number=round_num,
                    action_type="do_nothing",
                )

            # Shorter prompt for simplified processing
            feed_text = self.platform.format_feed_for_prompt(feed, round_num)
            prompt = (
                f"Du bist {persona.name}, {persona.occupation}. "
                f"Stil: {persona.posting_style.tone}.\n\n"
                f"{feed_text}\n\n"
                f"Wähle EINE Aktion: like_post, comment, oder do_nothing. "
                f"Wenn du kommentierst, schreibe maximal 2 Sätze."
            )

            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                tools=self.platform.get_tools_schema(),
                temperature=0.5,
                max_tokens=150,
            )
            self.usage.record(response)

            return self._parse_llm_response(response, persona.id, round_num, feed)

    async def _process_agent_observer(
        self, persona: Persona, round_num: int, agent_index: int
    ) -> AgentAction | None:
        """Rule-based processing for observers. No LLM call."""
        feed = await self.platform.generate_feed(
            persona.id, persona, round_num, feed_size=2
        )

        if not feed:
            return AgentAction(
                agent_id=persona.id,
                round_number=round_num,
                action_type="do_nothing",
            )

        # Simple rule: like a post if sentiment aligns with persona opinion
        state = self.agent_states[persona.id]
        for item in feed:
            opinion_match = abs(item.sentiment - state.current_sentiment) < 0.5
            if opinion_match and item.likes < 20:  # Don't pile on popular posts
                return AgentAction(
                    agent_id=persona.id,
                    round_number=round_num,
                    action_type="like_post",
                    target_post_id=item.post_id,
                )

        return AgentAction(
            agent_id=persona.id,
            round_number=round_num,
            action_type="do_nothing",
        )

    def _build_system_prompt(self, persona: Persona) -> str:
        """Build the system prompt for an agent. This part gets cached by OpenAI."""
        intro = (
            f"Du bist {persona.name}, {persona.age} Jahre alt, "
            f"{persona.occupation} aus {persona.region}, {persona.country}."
        )
        parts = [
            intro,
            "",
            "PERSÖNLICHKEIT:",
            f"- Kommunikationsstil: {persona.posting_style.tone}",
            f"- Posting-Frequenz: {persona.posting_style.frequency}",
        ]

        if persona.bio:
            parts.append(f"\nBIOGRAFIE: {persona.bio}")

        if persona.interests:
            parts.append(f"\nINTERESSEN: {', '.join(persona.interests[:5])}")

        parts.extend([
            "",
            "WICHTIGE REGELN:",
            "- Du postest NUR wenn du wirklich etwas zu sagen hast",
            f"- Dein Stil ist IMMER {persona.posting_style.tone}",
            "- Du änderst deine Grundmeinungen NICHT leichtfertig",
            "- Wähle genau EINE Aktion pro Runde",
            "- Alle Inhalte auf Deutsch",
            "",
            self.platform.get_platform_rules_prompt(),
        ])

        if persona.is_zealot:
            parts.append(
                "\nWICHTIG: Du bist in deinen Meinungen UNERSCHÜTTERLICH. "
                "Nichts ändert deine Haltung."
            )

        if persona.is_contrarian:
            parts.append("\nWICHTIG: Du neigst dazu, der Mehrheitsmeinung zu widersprechen.")

        return "\n".join(parts)

    def _build_user_prompt(
        self, persona: Persona, memory_text: str, feed_text: str, round_num: int
    ) -> str:
        """Build the user prompt with dynamic content (memory + feed)."""
        return (
            f"{memory_text}\n\n{feed_text}\n\n"
            f"Runde {round_num}/{self.config.round_count}. Was willst du tun?"
        )

    def _parse_llm_response(
        self,
        response,
        agent_id: str,
        round_num: int,
        feed: list,
    ) -> AgentAction:
        """Parse LLM response into an AgentAction. Falls back to do_nothing on error."""
        # Check for tool calls
        if response.tool_calls:
            tc = response.tool_calls[0]  # Take first tool call
            func_name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}

            return AgentAction(
                agent_id=agent_id,
                round_number=round_num,
                action_type=func_name,
                content=args.get("content"),
                target_post_id=args.get("post_id"),
                target_user_id=args.get("user_id"),
                hashtags=args.get("hashtags", []),
                importance_score=args.get("importance", 0.0),
            )

        # No tool call — fallback to do_nothing
        return AgentAction(
            agent_id=agent_id,
            round_number=round_num,
            action_type="do_nothing",
            is_fallback=True,
        )

    async def _emit_event(self, event: SimulationEvent) -> None:
        """Emit an event for live-streaming. Silent if no callback registered."""
        if self.event_callback:
            try:
                await self.event_callback(event)
            except Exception as e:
                logger.warning(f"Event emission failed: {e}")


async def create_and_run_simulation(
    config: SimulationConfig,
    personas: list[Persona],
    llm: LLMProvider,
    event_callback: EventCallback | None = None,
) -> SimulationResult:
    """Convenience function to set up and run a simulation end-to-end.

    Creates the DB, graph, platform, and engine, then runs the simulation.
    """
    from app.simulation.platforms.public import PublicNetworkPlatform

    # Create simulation DB
    db_path = f"/tmp/swaarm_sim_{config.simulation_id}.db"
    db = SimulationDB(db_path)
    await db.initialize()

    # Create social graph
    graph = SocialGraph(config.platform)
    graph.initialize(personas, seed=config.seed)

    # Create platform
    platform = PublicNetworkPlatform(db, graph)

    # Insert personas into DB
    users = [(p.id, p.name, p.model_dump_json(), "{}") for p in personas]
    await db.insert_users_batch(users)

    # Create and run engine
    engine = SimulationEngine(
        config=config,
        db=db,
        graph=graph,
        platform=platform,
        llm=llm,
        personas=personas,
        event_callback=event_callback,
    )

    return await engine.run()
