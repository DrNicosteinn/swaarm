"""Simulation service — orchestrates the full simulation lifecycle.

Connects Prompt Builder → Persona Generator → Simulation Engine.
Reports progress via callback for live status updates.
Also provides run_quick_start_job for the entity-pipeline flow.
"""

import asyncio
import json
import random as _rnd
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from app.core.config import settings
from app.llm.base import LLMUsageTracker
from app.llm.openai import OpenAIProvider
from app.models.simulation import (
    PlatformType,
    ScenarioControversity,
    SimulationConfig,
    SimulationResult,
    SimulationStatus,
)
from app.services.entity_enricher import EntityEnricher, EnrichmentResult
from app.services.prompt_builder import PromptBuilder, StructuredScenario
from app.services.smart_decision import (
    EnrichmentDecision,
    SmartDecisionEngine,
    SimulationDecision,
)
from app.simulation.engine import create_and_run_simulation
from app.simulation.personas import PersonaGenerationConfig, PersonaGenerator

ProgressCallback = Callable[..., None]

# Stores prepared simulation data between quick-start and configure phases
_prepared_simulations: dict[str, dict[str, Any]] = {}


class SimulationRequest(BaseModel):
    """Request to start a new simulation."""

    scenario: StructuredScenario
    platform: PlatformType = PlatformType.PUBLIC
    agent_count: int = Field(default=200, ge=10, le=100000)
    round_count: int = Field(default=50, ge=5, le=200)


class SimulationRecord(BaseModel):
    """Database record for a simulation."""

    id: str
    user_id: str
    status: SimulationStatus = SimulationStatus.PENDING
    scenario_text: str = ""
    scenario_type: str = "default"
    platform: str = "public"
    agent_count: int = 200
    round_count: int = 50
    current_round: int = 0
    total_cost_usd: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    failure_reason: str | None = None


WsBroadcast = Callable[..., Any]


async def run_simulation_job(
    user_id: str,
    request: SimulationRequest,
    simulation_id: str | None = None,
    progress_callback: ProgressCallback | None = None,
    ws_broadcast: WsBroadcast | None = None,
) -> SimulationResult:
    """Run a complete simulation end-to-end with progress reporting."""
    if not simulation_id:
        simulation_id = f"sim-{uuid.uuid4().hex[:12]}"

    def report(**kwargs):
        if progress_callback:
            progress_callback(**kwargs)

    logger.info(
        f"Starting simulation {simulation_id} for user {user_id}: "
        f"{request.agent_count} agents, {request.round_count} rounds, "
        f"platform={request.platform.value}"
    )

    # Phase 1: Setup
    report(phase="initializing", phase_detail="LLM-Provider wird erstellt...")
    llm = OpenAIProvider(api_key=settings.openai_api_key, model=settings.swaarm_llm_model)
    usage = LLMUsageTracker(model=settings.swaarm_llm_model)

    builder = PromptBuilder(llm)
    controversity_level = builder.get_controversity_level(request.scenario.controversity_score)
    controversity = ScenarioControversity(controversity_level)

    # Phase 2: Persona Generation
    report(
        phase="generating_personas",
        phase_detail=f"Generiere {request.agent_count} Personas...",
        personas_generated=0,
    )
    logger.info(f"Generating personas for simulation {simulation_id}...")

    persona_gen = PersonaGenerator(llm, usage_tracker=usage)
    persona_config = PersonaGenerationConfig(
        scenario_text=request.scenario.statement or request.scenario.context,
        scenario_type=request.scenario.scenario_type,
        target_count=request.agent_count,
        base_persona_count=min(500, request.agent_count),
        controversity=controversity,
        seed=42,
        company=request.scenario.company or "",
        industry=request.scenario.industry or "",
    )
    # Incremental graph building: grow the graph as personas are generated
    from app.simulation.graph import SocialGraph

    incremental_graph = SocialGraph(request.platform)
    all_personas_so_far: list = []
    _sent_node_ids: set[str] = set()
    _sent_edge_keys: set[str] = set()

    def on_persona_progress(count: int):
        report(
            phase="generating_personas",
            phase_detail=f"{count}/{request.agent_count} Personas generiert...",
            personas_generated=count,
        )

    # Sentiment bias by stakeholder role (makes graph colorful from start)
    _role_sentiment = {
        "employees": -0.4,
        "customers": -0.2,
        "media": -0.1,
        "competitors": 0.1,
        "regulators": 0.0,
        "investors": -0.3,
        "general_public": -0.1,
        "activists": -0.6,
        "politicians": -0.3,
    }
    # followerCount by tier (visual node size)
    _tier_followers = {
        "power_creator": 400,
        "active_responder": 120,
        "selective_engager": 50,
        "observer": 15,
    }
    import random as _rnd

    # Track community assignment by role order
    _role_to_community: dict[str, int] = {}
    _community_counter = 0

    async def on_persona_batch(new_personas: list) -> None:
        """Called per persona. Sends node immediately. Links come later."""
        nonlocal _community_counter
        all_personas_so_far.extend(new_personas)

        if not ws_broadcast:
            return

        # Build new nodes (no graph rebuild — just send the node)
        new_nodes = []
        for p in new_personas:
            if p.id not in _sent_node_ids:
                _sent_node_ids.add(p.id)
                tier_str = p.agent_tier.value if p.agent_tier else "observer"
                role = p.stakeholder_role or "general"
                if role not in _role_to_community:
                    _role_to_community[role] = _community_counter
                    _community_counter += 1

                base_sentiment = _role_sentiment.get(role, 0.0)
                sentiment = max(-1, min(1, base_sentiment + _rnd.uniform(-0.3, 0.3)))
                base_followers = _tier_followers.get(tier_str, 15)
                followers = max(5, int(base_followers * _rnd.uniform(0.5, 1.5)))
                new_nodes.append(
                    {
                        "id": p.id,
                        "label": p.name,
                        "communityId": _role_to_community[role],
                        "sentiment": round(sentiment, 2),
                        "followerCount": followers,
                        "tier": tier_str,
                        "role": role,
                        "occupation": p.occupation or "",
                    }
                )

        if new_nodes:
            await ws_broadcast(
                json.dumps(
                    {
                        "type": "round_complete",
                        "round": 0,
                        "data": {
                            "active_agents": 0,
                            "posts_created": 0,
                            "avg_sentiment": 0.0,
                            "cost_usd": 0.0,
                            "actions": [],
                            "new_nodes": new_nodes,
                            "new_links": [],  # Links come after all personas are done
                        },
                    }
                )
            )

    personas = await persona_gen.generate(
        persona_config,
        on_progress=on_persona_progress,
        on_batch=on_persona_batch,
    )
    report(
        phase="generating_personas",
        phase_detail=f"{len(personas)} Personas generiert",
        personas_generated=len(personas),
    )

    # Build graph ONCE with all personas, send all links
    incremental_graph.graph.clear()
    incremental_graph.initialize(personas, seed=42)
    logger.info(f"Graph built: {incremental_graph.get_graph_stats()}")

    if ws_broadcast:
        all_links = [{"source": u, "target": v, "type": "follow"} for u, v in incremental_graph.graph.edges()]
        await ws_broadcast(
            json.dumps(
                {
                    "type": "round_complete",
                    "round": 0,
                    "data": {
                        "active_agents": 0,
                        "posts_created": 0,
                        "avg_sentiment": 0.0,
                        "cost_usd": 0.0,
                        "actions": [],
                        "new_nodes": [],
                        "new_links": all_links,
                    },
                }
            )
        )

    # Phase 3: Simulation
    report(
        phase="simulating",
        phase_detail="Simulation startet...",
        current_round=0,
    )
    logger.info(f"Running simulation {simulation_id}...")

    sim_config = SimulationConfig(
        simulation_id=simulation_id,
        user_id=user_id,
        scenario_text=request.scenario.statement or "",
        scenario_structured=request.scenario.model_dump(),
        platform=request.platform,
        controversity=controversity,
        agent_count=request.agent_count,
        round_count=request.round_count,
        seed=42,
    )

    # Event callback that updates progress per round
    async def on_sim_event(event):
        if event.event_type == "round_complete":
            d = event.data
            report(
                phase="simulating",
                phase_detail=f"Runde {event.round}/{request.round_count}",
                current_round=event.round,
                posts_created=d.get("posts_created", 0),
                avg_sentiment=d.get("avg_sentiment", 0.0),
                cost_usd=usage.total_cost_usd,
            )

    result = await create_and_run_simulation(
        config=sim_config,
        personas=personas,
        llm=llm,
        event_callback=on_sim_event,
        seed_posts=request.scenario.seed_posts or None,
    )

    # Phase 4: Done
    report(
        phase="done",
        phase_detail="Simulation abgeschlossen",
        current_round=result.completed_rounds,
        cost_usd=result.total_cost_usd,
    )

    logger.info(
        f"Simulation {simulation_id} {result.status.value}: "
        f"{result.completed_rounds}/{result.total_rounds} rounds, "
        f"${result.total_cost_usd:.4f}"
    )

    return result


# ── Quick-Start Flow ─────────────────────────────────────────────────

# Entity type → color mapping for graph visualization
_ENTITY_TYPE_COLORS = {
    "real_person": "#10b981",  # green
    "real_company": "#6366f1",  # indigo
    "role": "#f59e0b",  # amber
    "institution": "#8b5cf6",  # purple
    "media_outlet": "#ec4899",  # pink
    "product": "#06b6d4",  # cyan
    "event": "#f97316",  # orange
}


async def run_quick_start_job(
    user_id: str,
    input_text: str,
    simulation_id: str,
    progress_callback: ProgressCallback | None = None,
    ws_broadcast: WsBroadcast | None = None,
) -> None:
    """Entity-pipeline flow: analyze → extract entities → enrich → generate personas.

    After persona generation, the job pauses. The simulation itself
    starts when run_simulation_phase() is called via the /configure endpoint.
    """

    def report(**kwargs):
        if progress_callback:
            progress_callback(**kwargs)

    logger.info(f"Quick-start {simulation_id} for user {user_id}")

    llm = OpenAIProvider(api_key=settings.openai_api_key, model=settings.swaarm_llm_model)
    usage = LLMUsageTracker(model=settings.swaarm_llm_model)

    # ── Phase 1: Smart Decision (analyze + entity extraction) ──
    report(phase="analyzing", phase_detail="Analysiere Fragestellung...")
    if ws_broadcast:
        await ws_broadcast(
            json.dumps(
                {
                    "type": "phase_changed",
                    "data": {"phase": "analyzing", "detail": "Analysiere Fragestellung..."},
                }
            )
        )

    engine = SmartDecisionEngine(llm, usage_tracker=usage)
    decision = await engine.analyze(input_text)
    logger.info(f"Smart decision: {decision.simulation_type}, {len(decision.entities)} entities")

    # ── Phase 2: Stream entities to graph (200ms stagger) ──
    report(
        phase="extracting_entities",
        phase_detail=f"{len(decision.entities)} Entitaeten erkannt",
        entities_found=len(decision.entities),
    )
    if ws_broadcast:
        await ws_broadcast(
            json.dumps(
                {
                    "type": "phase_changed",
                    "data": {
                        "phase": "extracting_entities",
                        "detail": f"{len(decision.entities)} Entitaeten erkannt",
                    },
                }
            )
        )

    # Build entity nodes and relationship links
    entity_name_to_id: dict[str, str] = {}
    for entity in decision.entities:
        entity_id = f"entity-{uuid.uuid4().hex[:8]}"
        entity_name_to_id[entity.name] = entity_id

    for entity in decision.entities:
        eid = entity_name_to_id[entity.name]
        node = {
            "id": eid,
            "label": entity.name,
            "communityId": 0,
            "sentiment": entity.sentiment_toward_scenario,
            "followerCount": int(entity.importance * 500),
            "tier": "power_creator",
            "role": entity.role_in_scenario,
            "occupation": entity.sub_type,
            "entityType": entity.entity_type.value,
            "subType": entity.sub_type,
            "personaSource": "real_enriched"
            if entity.enrichment == EnrichmentDecision.ENRICH
            else "role_based",
            "isEntity": True,
            "importance": entity.importance,
        }

        # Build relationship links for this entity
        links = []
        for rel in entity.relationships:
            target_id = entity_name_to_id.get(rel.target_entity_name)
            if target_id:
                links.append(
                    {
                        "source": eid,
                        "target": target_id,
                        "type": "entity_relation",
                        "label": rel.label,
                    }
                )

        if ws_broadcast:
            await ws_broadcast(
                json.dumps({"type": "entity_extracted", "data": {"node": node, "links": links}})
            )
        await asyncio.sleep(0.2)  # 200ms stagger for visual effect

    # ── Phase 3: Web Enrichment ──
    entities_to_enrich = [e for e in decision.entities if e.enrichment == EnrichmentDecision.ENRICH]
    enrichment_results: list[EnrichmentResult] = []

    if entities_to_enrich:
        report(
            phase="enriching",
            phase_detail=f"Recherchiere {len(entities_to_enrich)} Entitaeten...",
        )
        if ws_broadcast:
            await ws_broadcast(
                json.dumps(
                    {
                        "type": "phase_changed",
                        "data": {
                            "phase": "enriching",
                            "detail": f"Recherchiere {len(entities_to_enrich)} Entitaeten...",
                        },
                    }
                )
            )

        enricher = EntityEnricher(llm, usage_tracker=usage)
        _enriched_count = 0

        async def on_enrichment_progress(result: EnrichmentResult):
            eid = entity_name_to_id.get(result.entity_name, "")
            if ws_broadcast:
                if result.success:
                    # Update node with richer data
                    updated_node = {
                        "id": eid,
                        "label": result.verified_name or result.entity_name,
                        "occupation": result.verified_title or "",
                    }
                    await ws_broadcast(
                        json.dumps(
                            {
                                "type": "entity_enriched",
                                "data": {"entity_name": result.entity_name, "node": updated_node},
                            }
                        )
                    )
                else:
                    await ws_broadcast(
                        json.dumps(
                            {
                                "type": "enrichment_failed",
                                "data": {
                                    "entity_name": result.entity_name,
                                    "reason": "Recherche fehlgeschlagen",
                                },
                            }
                        )
                    )
            nonlocal _enriched_count
            if result.success:
                _enriched_count += 1
            report(entities_enriched=_enriched_count)

        enrichment_results = await enricher.enrich_batch(
            entities_to_enrich,
            scenario_context=input_text,
            on_progress=on_enrichment_progress,
            max_concurrent=3,
        )
        logger.info(
            f"Enrichment complete: {sum(1 for r in enrichment_results if r.success)}/{len(enrichment_results)} successful"
        )

    # ── Phase 4: Persona Generation ──
    report(
        phase="generating_personas",
        phase_detail="Generiere Personas...",
        personas_generated=0,
    )
    if ws_broadcast:
        await ws_broadcast(
            json.dumps(
                {
                    "type": "phase_changed",
                    "data": {"phase": "generating_personas", "detail": "Generiere Personas..."},
                }
            )
        )

    # Build scenario context from decision
    builder = PromptBuilder(llm)
    scenario = await builder.analyze_input(input_text)
    controversity_level = builder.get_controversity_level(scenario.controversity_score)
    controversity = ScenarioControversity(controversity_level)

    persona_gen = PersonaGenerator(llm, usage_tracker=usage)
    persona_config = PersonaGenerationConfig(
        scenario_text=input_text,
        scenario_type=decision.scenario_type,
        target_count=decision.persona_strategy.total or settings.default_agent_count,
        base_persona_count=min(500, decision.persona_strategy.total or settings.default_agent_count),
        controversity=controversity,
        seed=42,
        company=scenario.company or "",
        industry=scenario.industry or "",
    )

    # Role sentiment + follower mapping (reused from original flow)
    _role_sentiment = {
        "employees": -0.4,
        "customers": -0.2,
        "media": -0.1,
        "competitors": 0.1,
        "regulators": 0.0,
        "investors": -0.3,
        "general_public": -0.1,
        "activists": -0.6,
        "politicians": -0.3,
    }
    _tier_followers = {
        "power_creator": 400,
        "active_responder": 120,
        "selective_engager": 50,
        "observer": 15,
    }
    _role_to_community: dict[str, int] = {}
    _community_counter = len(decision.entities)  # Start after entity communities
    _sent_node_ids: set[str] = set()

    def on_persona_progress(count: int):
        report(
            phase="generating_personas",
            phase_detail=f"{count} Personas generiert...",
            personas_generated=count,
        )

    async def on_persona_batch(new_personas: list) -> None:
        nonlocal _community_counter
        if not ws_broadcast:
            return

        new_nodes = []
        new_links = []
        for p in new_personas:
            if p.id not in _sent_node_ids:
                _sent_node_ids.add(p.id)
                tier_str = p.agent_tier.value if p.agent_tier else "observer"
                role = p.stakeholder_role or "general"
                if role not in _role_to_community:
                    _role_to_community[role] = _community_counter
                    _community_counter += 1

                base_sentiment = _role_sentiment.get(role, 0.0)
                sentiment = max(-1, min(1, base_sentiment + _rnd.uniform(-0.3, 0.3)))
                base_followers = _tier_followers.get(tier_str, 15)
                followers = max(5, int(base_followers * _rnd.uniform(0.5, 1.5)))

                new_nodes.append(
                    {
                        "id": p.id,
                        "label": p.name,
                        "communityId": _role_to_community[role],
                        "sentiment": round(sentiment, 2),
                        "followerCount": followers,
                        "tier": tier_str,
                        "role": role,
                        "occupation": p.occupation or "",
                        "personaSource": p.persona_source.value
                        if hasattr(p, "persona_source")
                        else "generated",
                        "isEntity": False,
                    }
                )

                # Link persona to its source entity if applicable
                if p.source_entity_name and p.source_entity_name in entity_name_to_id:
                    new_links.append(
                        {
                            "source": p.id,
                            "target": entity_name_to_id[p.source_entity_name],
                            "type": "persona_entity",
                            "label": "",
                        }
                    )

        if new_nodes:
            await ws_broadcast(
                json.dumps({"type": "persona_batch", "data": {"nodes": new_nodes, "links": new_links}})
            )

    all_personas = await persona_gen.generate(
        persona_config,
        on_progress=on_persona_progress,
        on_batch=on_persona_batch,
        decision=decision,
        enrichment_results=enrichment_results,
    )

    # Build the social graph and send remaining links
    from app.simulation.graph import SocialGraph

    platform = PlatformType(decision.persona_strategy.recommended_platform)
    graph = SocialGraph(platform)
    graph.initialize(all_personas, seed=42)

    if ws_broadcast:
        all_links = [{"source": u, "target": v, "type": "follow"} for u, v in graph.graph.edges()]
        await ws_broadcast(json.dumps({"type": "persona_batch", "data": {"nodes": [], "links": all_links}}))

    # ── Phase 5: Wait for user config ──
    total_personas = len(all_personas)
    report(
        phase="configuring",
        phase_detail=f"{total_personas} Personas generiert. Bereit fuer Simulation.",
        personas_generated=total_personas,
        total_agents=total_personas,
        recommended_platform=decision.persona_strategy.recommended_platform,
    )
    if ws_broadcast:
        await ws_broadcast(
            json.dumps(
                {
                    "type": "phase_changed",
                    "data": {
                        "phase": "configuring",
                        "detail": f"{total_personas} Personas generiert. Bereit fuer Simulation.",
                        "persona_count": total_personas,
                        "recommended_platform": decision.persona_strategy.recommended_platform,
                    },
                }
            )
        )

    # Store prepared data for the simulation phase
    _prepared_simulations[simulation_id] = {
        "personas": all_personas,
        "graph": graph,
        "scenario": scenario,
        "decision": decision,
        "usage": usage,
        "controversity": controversity,
    }

    logger.info(
        f"Quick-start {simulation_id}: {total_personas} personas ready, "
        f"awaiting config. Cost so far: ${usage.total_cost_usd:.4f}"
    )


async def run_simulation_phase(
    simulation_id: str,
    user_id: str,
    platform: PlatformType,
    round_count: int,
    progress_callback: ProgressCallback | None = None,
    ws_broadcast: WsBroadcast | None = None,
) -> SimulationResult:
    """Run the actual simulation after personas are generated and user configured platform + rounds."""
    prepared = _prepared_simulations.pop(simulation_id, None)
    if not prepared:
        raise ValueError(f"No prepared simulation data for {simulation_id}")

    def report(**kwargs):
        if progress_callback:
            progress_callback(**kwargs)

    personas = prepared["personas"]
    scenario = prepared["scenario"]
    usage = prepared["usage"]
    controversity = prepared["controversity"]

    llm = OpenAIProvider(api_key=settings.openai_api_key, model=settings.swaarm_llm_model)

    report(phase="simulating", phase_detail="Simulation startet...", current_round=0)
    if ws_broadcast:
        await ws_broadcast(
            json.dumps(
                {"type": "phase_changed", "data": {"phase": "simulating", "detail": "Simulation startet..."}}
            )
        )

    sim_config = SimulationConfig(
        simulation_id=simulation_id,
        user_id=user_id,
        scenario_text=scenario.statement or "",
        scenario_structured=scenario.model_dump(),
        platform=platform,
        controversity=controversity,
        agent_count=len(personas),
        round_count=round_count,
        seed=42,
    )

    async def on_sim_event(event):
        if event.event_type == "round_complete":
            d = event.data
            report(
                phase="simulating",
                phase_detail=f"Runde {event.round}/{round_count}",
                current_round=event.round,
                posts_created=d.get("posts_created", 0),
                avg_sentiment=d.get("avg_sentiment", 0.0),
                cost_usd=usage.total_cost_usd,
            )

    result = await create_and_run_simulation(
        config=sim_config,
        personas=personas,
        llm=llm,
        event_callback=on_sim_event,
        seed_posts=scenario.seed_posts or None,
    )

    report(
        phase="done",
        phase_detail="Simulation abgeschlossen",
        current_round=result.completed_rounds,
        cost_usd=result.total_cost_usd,
    )

    logger.info(
        f"Simulation {simulation_id} {result.status.value}: "
        f"{result.completed_rounds}/{result.total_rounds} rounds, "
        f"${result.total_cost_usd:.4f}"
    )

    return result
