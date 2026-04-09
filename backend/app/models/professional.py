"""Professional profile model for LinkedIn-like simulation."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class SeniorityLevel(StrEnum):
    """LinkedIn-aligned seniority levels."""

    INTERN = "intern"
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    DIRECTOR = "director"
    VP = "vp"
    C_LEVEL = "c_level"
    OWNER = "owner"


class ProfessionalProfile(BaseModel):
    """LinkedIn-specific professional identity. None for public-network personas."""

    job_title: str
    company_name: str = ""
    company_size: Literal["1-10", "11-50", "51-200", "201-1000", "1001-5000", "5000+"] = "51-200"
    industry_sector: str = ""
    seniority_level: SeniorityLevel = SeniorityLevel.MID
    years_experience: int = Field(default=5, ge=0, le=50)
    expertise_topics: list[str] = Field(default_factory=list)
    headline: str = ""
    connection_count: int = Field(default=400, ge=0, le=30000)
    compliance_awareness: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="How cautious about posting (high in banking/pharma)",
    )
    thought_leadership_score: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="How much they position as industry thought leader",
    )
