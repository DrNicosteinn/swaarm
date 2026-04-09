"""Persona models — static agent identity that doesn't change during simulation."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.models.professional import ProfessionalProfile


class AgentTier(StrEnum):
    """Agent activity tier based on scenario-driven distribution."""

    POWER_CREATOR = "power_creator"
    ACTIVE_RESPONDER = "active_responder"
    SELECTIVE_ENGAGER = "selective_engager"
    OBSERVER = "observer"


class PersonaSource(StrEnum):
    """How this persona was created."""

    REAL_ENRICHED = "real_enriched"  # Real person, web-enriched with Serper data
    REAL_MINIMAL = "real_minimal"  # Mentioned in document, limited data
    ROLE_BASED = "role_based"  # Typical role, not a real person
    GENERATED = "generated"  # Fully synthetic from demographics


class BigFive(BaseModel):
    """Big Five personality traits, each 0.0-1.0."""

    openness: float = Field(ge=0.0, le=1.0)
    conscientiousness: float = Field(ge=0.0, le=1.0)
    extraversion: float = Field(ge=0.0, le=1.0)
    agreeableness: float = Field(ge=0.0, le=1.0)
    neuroticism: float = Field(ge=0.0, le=1.0)


class PostingStyle(BaseModel):
    """How this persona communicates on social media."""

    frequency: Literal[
        "daily",
        "weekly",
        "monthly",
        "rarely",
        # German variants (LLM sometimes responds in German)
        "täglich",
        "taeglich",
        "wöchentlich",
        "woechentlich",
        "monatlich",
        "selten",
    ] = "weekly"
    tone: str = "sachlich"  # e.g. sachlich, emotional, provokativ, humorvoll
    typical_topics: list[str] = Field(default_factory=list)
    avg_post_length: Literal["short", "medium", "long"] = "medium"


class OpinionSeeds(BaseModel):
    """Core opinion dimensions that drive agent behavior. Each 0.0-1.0."""

    trust_institutions: float = Field(default=0.5, ge=0.0, le=1.0)
    environmental_concern: float = Field(default=0.5, ge=0.0, le=1.0)
    tech_optimism: float = Field(default=0.5, ge=0.0, le=1.0)
    economic_anxiety: float = Field(default=0.5, ge=0.0, le=1.0)
    social_progressivism: float = Field(default=0.5, ge=0.0, le=1.0)


class Persona(BaseModel):
    """A complete persona definition. Static — created once, never mutated."""

    # Identity
    id: str
    name: str
    age: int = Field(ge=18, le=95)
    gender: str
    country: Literal["DE", "CH", "AT"]
    region: str  # e.g. "Zürich", "Bayern", "Wien"
    city_type: Literal["urban", "suburban", "rural"] = "urban"

    # Professional
    occupation: str
    industry: str = ""
    seniority: Literal["Student", "Junior", "Mid", "Senior", "Executive", "Retired"] = "Mid"
    education: str = ""

    # Personality
    big_five: BigFive
    sinus_milieu: str = ""

    # Social media behavior
    agent_tier: AgentTier = AgentTier.ACTIVE_RESPONDER
    posting_style: PostingStyle = Field(default_factory=PostingStyle)
    opinions: OpinionSeeds = Field(default_factory=OpinionSeeds)
    interests: list[str] = Field(default_factory=list)

    # Stakeholder role (scenario-specific)
    stakeholder_role: str = "general_public"
    stakeholder_subtype: str = ""

    # Bio for LLM prompt
    bio: str = ""

    # Professional network specific (optional, populated for LinkedIn simulation)
    professional_profile: ProfessionalProfile | None = None

    # Persona source tracking
    persona_source: PersonaSource = PersonaSource.GENERATED
    source_entity_name: str | None = None  # Link to ExtractedEntity that seeded this persona
    enrichment_sources: list[str] = Field(default_factory=list)  # e.g. ["web_search", "document"]

    # Flags
    is_zealot: bool = False  # Opinion never changes
    is_contrarian: bool = False  # Tends to disagree with majority
