"""Simulation API endpoints — analyze input, start simulations, check status."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import AuthUser, get_current_user
from app.core.config import settings
from app.llm.openai import OpenAIProvider
from app.models.simulation import SimulationStatus
from app.services.prompt_builder import PromptBuilder, StructuredScenario
from app.services.simulation_service import SimulationRequest, run_simulation_job

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


@router.post("/analyze-input")
async def analyze_input(
    request: AnalyzeInputRequest,
    user: AuthUser = Depends(get_current_user),
) -> AnalyzeInputResponse:
    """Analyze free-text input and extract structured scenario."""
    llm = OpenAIProvider(api_key=settings.openai_api_key, model=settings.swaarm_llm_model)
    builder = PromptBuilder(llm)
    scenario = await builder.analyze_input(request.text)
    return AnalyzeInputResponse(
        scenario=scenario,
        needs_improvement=len(scenario.missing_fields) > 0,
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

    background_tasks.add_task(
        _run_simulation_background, simulation_id, user.id, request
    )

    return StartSimulationResponse(
        simulation_id=simulation_id,
        status="pending",
        message="Simulation gestartet.",
    )


async def _run_simulation_background(
    simulation_id: str, user_id: str, request: SimulationRequest
) -> None:
    """Background task that runs the simulation."""
    _update_job(simulation_id, status=SimulationStatus.RUNNING.value)

    def progress_cb(**kwargs):
        _update_job(simulation_id, **kwargs)

    try:
        result = await run_simulation_job(
            user_id, request,
            simulation_id=simulation_id,
            progress_callback=progress_cb,
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
