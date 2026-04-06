"""Simulation API endpoints — analyze input, start simulations, check status."""

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


class AnalyzeInputRequest(BaseModel):
    """Request body for scenario analysis."""

    text: str


class AnalyzeInputResponse(BaseModel):
    """Response from scenario analysis."""

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
    """Request body for improvement suggestions."""

    scenario: StructuredScenario


@router.post("/suggest-improvements")
async def suggest_improvements(
    request: SuggestImprovementsRequest,
    user: AuthUser = Depends(get_current_user),
) -> list[str]:
    """Generate improvement suggestions for an incomplete scenario."""
    llm = OpenAIProvider(api_key=settings.openai_api_key, model=settings.swaarm_llm_model)
    builder = PromptBuilder(llm)

    suggestions = await builder.suggest_improvements(request.scenario)
    return suggestions


class StartSimulationResponse(BaseModel):
    """Response when starting a simulation."""

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
    import uuid

    simulation_id = f"sim-{uuid.uuid4().hex[:12]}"

    # Track the job
    _simulation_jobs[simulation_id] = {
        "status": SimulationStatus.PENDING.value,
        "user_id": user.id,
        "current_round": 0,
        "total_rounds": request.round_count,
        "result": None,
    }

    # Run in background
    background_tasks.add_task(
        _run_simulation_background,
        simulation_id,
        user.id,
        request,
    )

    return StartSimulationResponse(
        simulation_id=simulation_id,
        status="pending",
        message="Simulation gestartet. Nutze /api/simulation/status/{id} für Updates.",
    )


async def _run_simulation_background(
    simulation_id: str,
    user_id: str,
    request: SimulationRequest,
) -> None:
    """Background task that runs the simulation."""
    _simulation_jobs[simulation_id]["status"] = SimulationStatus.RUNNING.value

    try:
        result = await run_simulation_job(user_id, request, simulation_id=simulation_id)
        _simulation_jobs[simulation_id]["status"] = result.status.value
        _simulation_jobs[simulation_id]["result"] = result.model_dump()
        _simulation_jobs[simulation_id]["current_round"] = result.completed_rounds
    except Exception as e:
        _simulation_jobs[simulation_id]["status"] = SimulationStatus.FAILED.value
        _simulation_jobs[simulation_id]["error"] = str(e)


@router.get("/status/{simulation_id}")
async def get_simulation_status(
    simulation_id: str,
    user: AuthUser = Depends(get_current_user),
) -> dict:
    """Get the status of a running or completed simulation."""
    job = _simulation_jobs.get(simulation_id)
    if not job:
        raise HTTPException(status_code=404, detail="Simulation nicht gefunden")
    if job["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Zugriff verweigert")

    return {
        "simulation_id": simulation_id,
        "status": job["status"],
        "current_round": job.get("current_round", 0),
        "total_rounds": job.get("total_rounds", 0),
    }


@router.get("/list")
async def list_simulations(
    user: AuthUser = Depends(get_current_user),
) -> list[dict]:
    """List all simulations for the current user."""
    user_sims = [
        {
            "simulation_id": sid,
            "status": job["status"],
            "current_round": job.get("current_round", 0),
            "total_rounds": job.get("total_rounds", 0),
        }
        for sid, job in _simulation_jobs.items()
        if job["user_id"] == user.id
    ]
    return user_sims
