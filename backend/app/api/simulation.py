"""Simulation API endpoints — analyze input, start simulations, check status."""

import json
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import AuthUser, get_current_user
from app.core.config import settings
from app.llm.base import LLMUsageTracker
from app.llm.openai import OpenAIProvider
from app.models.simulation import PlatformType, SimulationStatus
from app.services.prompt_builder import PromptBuilder, StructuredScenario
from app.services.simulation_service import SimulationRequest, run_simulation_job, run_quick_start_job
from app.services.smart_decision import SmartDecisionEngine, SimulationDecision
from app.services.ws_manager import ws_manager

router = APIRouter()

# In-memory simulation status tracking (will be replaced by Supabase in production)
_simulation_jobs: dict[str, dict] = {}


def _update_job(simulation_id: str, **kwargs) -> None:
    """Update job status fields. Called by the SimulationService via callback."""
    job = _simulation_jobs.get(simulation_id)
    if job:
        job.update(kwargs)


class AnalyzeInputRequest(BaseModel):
    text: str


class AnalyzeInputResponse(BaseModel):
    scenario: StructuredScenario
    needs_improvement: bool
    decision: SimulationDecision | None = None


@router.post("/analyze-input")
async def analyze_input(
    request: AnalyzeInputRequest,
    user: AuthUser = Depends(get_current_user),
) -> AnalyzeInputResponse:
    """Analyze free-text input: extract scenario + run smart decision for entities."""
    llm = OpenAIProvider(api_key=settings.openai_api_key, model=settings.swaarm_llm_model)
    usage = LLMUsageTracker(model=settings.swaarm_llm_model)

    # Step 1: Extract structured scenario (existing)
    builder = PromptBuilder(llm)
    scenario = await builder.analyze_input(request.text)

    # Step 2: Smart decision (entity extraction + strategy)
    engine = SmartDecisionEngine(llm, usage_tracker=usage)
    decision = await engine.analyze(
        request.text,
        structured_scenario=scenario.model_dump(),
    )

    return AnalyzeInputResponse(
        scenario=scenario,
        needs_improvement=len(decision.follow_up_questions) > 0,
        decision=decision,
    )


class SuggestImprovementsRequest(BaseModel):
    scenario: StructuredScenario


@router.post("/suggest-improvements")
async def suggest_improvements(
    request: SuggestImprovementsRequest,
    user: AuthUser = Depends(get_current_user),
) -> list[str]:
    """Generate improvement suggestions for an incomplete scenario."""
    llm = OpenAIProvider(api_key=settings.openai_api_key, model=settings.swaarm_llm_model)
    builder = PromptBuilder(llm)
    return await builder.suggest_improvements(request.scenario)


class StartSimulationResponse(BaseModel):
    simulation_id: str
    status: str
    message: str


@router.post("/start")
async def start_simulation(
    request: SimulationRequest,
    background_tasks: BackgroundTasks,
    user: AuthUser = Depends(get_current_user),
) -> StartSimulationResponse:
    """Start a new simulation as a background job."""
    simulation_id = f"sim-{uuid.uuid4().hex[:12]}"

    _simulation_jobs[simulation_id] = {
        "status": SimulationStatus.PENDING.value,
        "user_id": user.id,
        # Phase tracking
        "phase": "initializing",
        "phase_detail": "Simulation wird vorbereitet...",
        # Progress
        "current_round": 0,
        "total_rounds": request.round_count,
        "total_agents": request.agent_count,
        "personas_generated": 0,
        # Stats
        "posts_created": 0,
        "comments_created": 0,
        "likes_created": 0,
        "avg_sentiment": 0.0,
        "cost_usd": 0.0,
        # Result
        "result": None,
    }

    background_tasks.add_task(_run_simulation_background, simulation_id, user.id, request)

    return StartSimulationResponse(
        simulation_id=simulation_id,
        status="pending",
        message="Simulation gestartet.",
    )


async def _run_simulation_background(simulation_id: str, user_id: str, request: SimulationRequest) -> None:
    """Background task that runs the simulation."""
    _update_job(simulation_id, status=SimulationStatus.RUNNING.value)

    def progress_cb(**kwargs):
        _update_job(simulation_id, **kwargs)

    async def ws_broadcast(message: str):
        """Broadcast a message to all WS clients watching this simulation."""
        await ws_manager.broadcast(simulation_id, message)

    try:
        result = await run_simulation_job(
            user_id,
            request,
            simulation_id=simulation_id,
            progress_callback=progress_cb,
            ws_broadcast=ws_broadcast,
        )
        _update_job(
            simulation_id,
            status=result.status.value,
            phase="done",
            phase_detail="Simulation abgeschlossen",
            current_round=result.completed_rounds,
            cost_usd=result.total_cost_usd,
        )
    except Exception as e:
        _update_job(
            simulation_id,
            status=SimulationStatus.FAILED.value,
            phase="error",
            phase_detail=str(e)[:200],
        )


# ── Quick-Start Flow ─────────────────────────────────────────────────


class QuickStartRequest(BaseModel):
    input_text: str
    additional_context: str = ""  # Answers to follow-up questions


class QuickStartResponse(BaseModel):
    simulation_id: str
    status: str
    message: str


@router.post("/quick-start")
async def quick_start(
    request: QuickStartRequest,
    background_tasks: BackgroundTasks,
    user: AuthUser = Depends(get_current_user),
) -> QuickStartResponse:
    """Start the full entity pipeline: analyze → enrich → generate personas.

    WebSocket streams all progress events. After persona generation,
    the simulation pauses and waits for /configure to set platform + rounds.
    """
    simulation_id = f"sim-{uuid.uuid4().hex[:12]}"

    combined_text = request.input_text
    if request.additional_context:
        combined_text += f"\n\nZusaetzlicher Kontext:\n{request.additional_context}"

    _simulation_jobs[simulation_id] = {
        "status": SimulationStatus.PENDING.value,
        "user_id": user.id,
        "phase": "analyzing",
        "phase_detail": "Analysiere Fragestellung...",
        "current_round": 0,
        "total_rounds": 0,
        "total_agents": 0,
        "personas_generated": 0,
        "entities_found": 0,
        "entities_enriched": 0,
        "posts_created": 0,
        "comments_created": 0,
        "likes_created": 0,
        "avg_sentiment": 0.0,
        "cost_usd": 0.0,
        "result": None,
        # Quick-start specific
        "input_text": combined_text,
        "awaiting_config": False,
        "recommended_platform": "public",
    }

    background_tasks.add_task(_run_quick_start_background, simulation_id, user.id, combined_text)

    return QuickStartResponse(
        simulation_id=simulation_id,
        status="pending",
        message="Entity-Pipeline gestartet.",
    )


async def _run_quick_start_background(simulation_id: str, user_id: str, input_text: str) -> None:
    """Background task for quick-start: analyze → enrich → generate personas."""
    _update_job(simulation_id, status=SimulationStatus.RUNNING.value)

    def progress_cb(**kwargs):
        _update_job(simulation_id, **kwargs)

    async def ws_broadcast_fn(message: str):
        await ws_manager.broadcast(simulation_id, message)

    try:
        await run_quick_start_job(
            user_id=user_id,
            input_text=input_text,
            simulation_id=simulation_id,
            progress_callback=progress_cb,
            ws_broadcast=ws_broadcast_fn,
        )
        # After persona generation, simulation pauses and waits for configure
        _update_job(simulation_id, awaiting_config=True)
    except Exception as e:
        _update_job(
            simulation_id,
            status=SimulationStatus.FAILED.value,
            phase="error",
            phase_detail=str(e)[:200],
        )


class ConfigureSimulationRequest(BaseModel):
    platform: PlatformType = PlatformType.PUBLIC
    round_count: int = Field(default=50, ge=5, le=200)


@router.post("/configure/{simulation_id}")
async def configure_simulation(
    simulation_id: str,
    request: ConfigureSimulationRequest,
    background_tasks: BackgroundTasks,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Configure and start the simulation after persona generation."""
    job = _simulation_jobs.get(simulation_id)
    if not job:
        raise HTTPException(status_code=404, detail="Simulation nicht gefunden")
    if job["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Zugriff verweigert")
    if not job.get("awaiting_config"):
        raise HTTPException(status_code=400, detail="Simulation wartet nicht auf Konfiguration")

    _update_job(
        simulation_id,
        awaiting_config=False,
        total_rounds=request.round_count,
        phase="simulating",
        phase_detail="Simulation startet...",
    )

    # The quick-start job stored prepared data in the job dict
    background_tasks.add_task(
        _run_simulation_after_config,
        simulation_id,
        user.id,
        request.platform,
        request.round_count,
    )

    return {"status": "started", "message": "Simulation gestartet"}


async def _run_simulation_after_config(
    simulation_id: str,
    user_id: str,
    platform: PlatformType,
    round_count: int,
) -> None:
    """Run the actual simulation after user configured platform + rounds."""
    from app.services.simulation_service import run_simulation_phase

    def progress_cb(**kwargs):
        _update_job(simulation_id, **kwargs)

    async def ws_broadcast_fn(message: str):
        await ws_manager.broadcast(simulation_id, message)

    job = _simulation_jobs.get(simulation_id)
    if not job:
        return

    try:
        result = await run_simulation_phase(
            simulation_id=simulation_id,
            user_id=user_id,
            platform=platform,
            round_count=round_count,
            progress_callback=progress_cb,
            ws_broadcast=ws_broadcast_fn,
        )
        _update_job(
            simulation_id,
            status=result.status.value,
            phase="done",
            phase_detail="Simulation abgeschlossen",
            current_round=result.completed_rounds,
            cost_usd=result.total_cost_usd,
        )
    except Exception as e:
        _update_job(
            simulation_id,
            status=SimulationStatus.FAILED.value,
            phase="error",
            phase_detail=str(e)[:200],
        )


@router.get("/status/{simulation_id}")
async def get_simulation_status(
    simulation_id: str,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Get detailed status of a simulation including phase info."""
    job = _simulation_jobs.get(simulation_id)
    if not job:
        raise HTTPException(status_code=404, detail="Simulation nicht gefunden")
    if job["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Zugriff verweigert")

    return {
        "simulation_id": simulation_id,
        "status": job["status"],
        "phase": job.get("phase", "unknown"),
        "phase_detail": job.get("phase_detail", ""),
        "current_round": job.get("current_round", 0),
        "total_rounds": job.get("total_rounds", 0),
        "total_agents": job.get("total_agents", 0),
        "personas_generated": job.get("personas_generated", 0),
        "posts_created": job.get("posts_created", 0),
        "comments_created": job.get("comments_created", 0),
        "likes_created": job.get("likes_created", 0),
        "avg_sentiment": job.get("avg_sentiment", 0.0),
        "cost_usd": job.get("cost_usd", 0.0),
    }


@router.get("/list")
async def list_simulations(
    user: AuthUser = Depends(get_current_user),
) -> list[dict]:
    """List all simulations for the current user."""
    return [
        {
            "simulation_id": sid,
            "status": job["status"],
            "phase": job.get("phase", "unknown"),
            "current_round": job.get("current_round", 0),
            "total_rounds": job.get("total_rounds", 0),
        }
        for sid, job in _simulation_jobs.items()
        if job["user_id"] == user.id
    ]
