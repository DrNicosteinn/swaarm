"""Action models — what agents can do on the simulated platforms."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PublicNetworkAction(StrEnum):
    """Actions available on the public network (Twitter-like)."""

    CREATE_POST = "create_post"
    LIKE = "like_post"
    REPOST = "repost"
    COMMENT = "comment"
    FOLLOW = "follow_user"
    DO_NOTHING = "do_nothing"


class ProfessionalNetworkAction(StrEnum):
    """Actions available on the professional network (LinkedIn-like)."""

    POST = "create_post"
    ARTICLE = "create_article"
    REACT_LIKE = "react_like"
    REACT_CELEBRATE = "react_celebrate"
    REACT_INSIGHTFUL = "react_insightful"
    REACT_FUNNY = "react_funny"
    REACT_LOVE = "react_love"
    REACT_SUPPORT = "react_support"
    COMMENT = "comment"
    REPLY = "reply"
    SHARE = "share"
    CONNECT = "connect"
    FOLLOW = "follow"
    ENDORSE = "endorse"
    DO_NOTHING = "do_nothing"


class AgentAction(BaseModel):
    """A single action taken by an agent in a round."""

    agent_id: str
    round_number: int
    action_type: str  # One of the action enums above
    content: str | None = None  # Text content for posts/comments
    target_post_id: str | None = None  # For likes, comments, reposts
    target_user_id: str | None = None  # For follows, connects
    hashtags: list[str] = Field(default_factory=list)
    importance_score: float = Field(
        default=0.0, ge=0.0, le=10.0, description="Self-assessed importance of this action"
    )
    reaction_type: str | None = None  # For LinkedIn reactions (celebrate, insightful, etc.)
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_fallback: bool = False  # True if this was a fallback due to LLM error


class FeedItem(BaseModel):
    """A single post/item in an agent's feed."""

    post_id: str
    author_id: str
    author_name: str
    content: str
    created_round: int
    likes: int = 0
    comments: int = 0
    reposts: int = 0
    sentiment: float = 0.0  # -1.0 to 1.0
    has_media: bool = False
    has_external_link: bool = False
    content_format: str = "text"  # text, image, carousel, video, link
    hashtags: list[str] = Field(default_factory=list)

    # Professional network additions (optional)
    reaction_type: str | None = None  # like, celebrate, insightful, support, love, funny
    via_connection_id: str | None = None  # "You see this because X commented"
    via_connection_name: str | None = None
    author_headline: str | None = None  # e.g. "VP Engineering at Acme"
