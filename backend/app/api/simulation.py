"""Simulation API endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import AuthUser, get_current_user
from app.core.config import settings
from app.llm.openai import OpenAIProvider
from app.services.prompt_builder import PromptBuilder, StructuredScenario

router = APIRouter()


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
    llm = OpenAIProvider(api_key=settings.openai_api_key, model=settings.default_llm_model)
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
    llm = OpenAIProvider(api_key=settings.openai_api_key, model=settings.default_llm_model)
    builder = PromptBuilder(llm)

    suggestions = await builder.suggest_improvements(request.scenario)
    return suggestions
