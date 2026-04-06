"""Simulation service — orchestrates the full simulation lifecycle.

Connects Prompt Builder → Persona Generator → Simulation Engine.
Reports progress via callback for live status updates.
"""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

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
from app.services.prompt_builder import PromptBuilder, StructuredScenario
from app.simulation.engine import create_and_run_simulation
from app.simulation.personas import PersonaGenerationConfig, PersonaGenerator

ProgressCallback = Callable[..., None]


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


async def run_simulation_job(
    user_id: str,
    request: SimulationRequest,
    simulation_id: str | None = None,
    progress_callback: ProgressCallback | None = None,
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
    )
    personas = await persona_gen.generate(persona_config)
    report(
        phase="generating_personas",
        phase_detail=f"{len(personas)} Personas generiert",
        personas_generated=len(personas),
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
