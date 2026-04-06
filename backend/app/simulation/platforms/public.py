"""Public network platform (Twitter-like).

Simulates a public social network with short posts, likes, reposts,
comments, and follows. Feed algorithm based on Twitter's open-sourced
engagement weights.
"""

import json
import math
import random
import uuid

from app.models.actions import AgentAction, FeedItem
from app.models.persona import Persona
from app.simulation.database import SimulationDB
from app.simulation.graph import SocialGraph
from app.simulation.platforms.base import PlatformBase

# Twitter open-source engagement weights
ENGAGEMENT_WEIGHTS = {
    "like": 1.0,
    "retweet": 20.0,
    "reply": 13.5,
    "bookmark": 10.0,
    "quote": 15.0,
}

RECENCY_HALF_LIFE_ROUNDS = 3  # Post loses half its score after 3 rounds


class PublicNetworkPlatform(PlatformBase):
    """Twitter-like public social network simulation."""

    def get_platform_name(self) -> str:
        return "Öffentliches Netzwerk"

    def get_action_types(self) -> list[str]:
        return ["create_post", "like_post", "repost", "comment", "follow_user", "do_nothing"]

    def get_tools_schema(self) -> list[dict]:
        """OpenAI function calling tools for Twitter-like actions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_post",
                    "description": "Erstelle einen neuen Post im öffentlichen Netzwerk.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Der Posttext (max 280 Zeichen)",
                            },
                            "hashtags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optionale Hashtags",
                            },
                        },
                        "required": ["content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "like_post",
                    "description": "Like einen Post.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "post_id": {"type": "string", "description": "ID des Posts"},
                        },
                        "required": ["post_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "repost",
                    "description": "Teile einen Post (Repost).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "post_id": {"type": "string", "description": "ID des Posts"},
                        },
                        "required": ["post_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "comment",
                    "description": "Kommentiere einen Post.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "post_id": {"type": "string", "description": "ID des Posts"},
                            "content": {"type": "string", "description": "Dein Kommentar"},
                        },
                        "required": ["post_id", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "follow_user",
                    "description": "Folge einem anderen User.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "ID des Users"},
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "do_nothing",
                    "description": "Nichts tun — nur beobachten.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]

    async def generate_feed(
        self,
        agent_id: str,
        agent_persona: Persona,
        current_round: int,
        feed_size: int = 5,
    ) -> list[FeedItem]:
        """Generate a personalized feed using Twitter-like ranking."""
        # Get all recent posts
        all_posts = await self.db.get_posts_for_feed(max_round=current_round, limit=200)
        if not all_posts:
            return []

        # Get who this agent follows
        following = set(self.graph.get_following(agent_id))

        # Score each post
        scored_posts: list[tuple[dict, float]] = []
        for post in all_posts:
            if post["author_id"] == agent_id:
                continue  # Don't show own posts
            score = self._score_post(post, agent_id, agent_persona, current_round, following)
            scored_posts.append((post, score))

        # Sort by score
        scored_posts.sort(key=lambda x: x[1], reverse=True)

        # Feed assembly: 85% relevant + 15% serendipity
        n_relevant = max(1, int(feed_size * 0.85))
        n_diverse = feed_size - n_relevant

        feed_posts = [p for p, _ in scored_posts[:n_relevant]]

        # Diverse: pick from lower-ranked posts, preferring different communities
        agent_community = self.graph.get_community(agent_id)
        tail = scored_posts[n_relevant:]
        cross_community = [
            p for p, _ in tail
            if self.graph.get_community(p["author_id"]) != agent_community
        ]
        if len(cross_community) >= n_diverse:
            feed_posts.extend(random.sample(cross_community, n_diverse))
        elif tail:
            feed_posts.extend([p for p, _ in tail[:n_diverse]])

        # Convert to FeedItems
        return [self._to_feed_item(p) for p in feed_posts[:feed_size]]

    def _score_post(
        self,
        post: dict,
        viewer_id: str,
        viewer_persona: Persona,
        current_round: int,
        following: set[str],
    ) -> float:
        """Score a post for feed ranking using Twitter engagement weights."""
        # Engagement score (log-dampened)
        raw_engagement = (
            post.get("likes", 0) * ENGAGEMENT_WEIGHTS["like"]
            + post.get("reposts", 0) * ENGAGEMENT_WEIGHTS["retweet"]
            + post.get("comments", 0) * ENGAGEMENT_WEIGHTS["reply"]
        )
        engagement = 1.0 + math.log1p(raw_engagement)

        # Recency decay
        age = current_round - post.get("created_round", 0)
        recency = 2.0 ** (-age / RECENCY_HALF_LIFE_ROUNDS)

        # Social proximity
        author_id = post["author_id"]
        if author_id in following:
            proximity = 1.0
        elif self.graph.get_community(viewer_id) == self.graph.get_community(author_id):
            proximity = 0.3
        else:
            proximity = 0.1

        # Topic relevance (simplified: based on hashtag overlap)
        post_tags = set(json.loads(post.get("hashtags", "[]")))
        viewer_interests = set(viewer_persona.interests)
        if post_tags and viewer_interests:
            overlap = len(post_tags & viewer_interests) / max(len(post_tags | viewer_interests), 1)
            topic = 0.3 + 0.7 * overlap
        else:
            topic = 0.5

        # Link penalty
        link_penalty = 0.4 if post.get("has_external_link") else 1.0

        return engagement * recency * proximity * topic * link_penalty

    def _to_feed_item(self, post: dict) -> FeedItem:
        """Convert a DB post dict to a FeedItem."""
        return FeedItem(
            post_id=post["id"],
            author_id=post["author_id"],
            author_name=post.get("author_name", post["author_id"]),
            content=post["content"],
            created_round=post["created_round"],
            likes=post.get("likes", 0),
            comments=post.get("comments", 0),
            reposts=post.get("reposts", 0),
            sentiment=post.get("sentiment", 0.0),
            has_media=bool(post.get("has_media")),
            has_external_link=bool(post.get("has_external_link")),
            content_format=post.get("content_format", "text"),
            hashtags=json.loads(post.get("hashtags", "[]")),
        )

    def format_feed_for_prompt(self, feed: list[FeedItem], current_round: int) -> str:
        """Serialize feed into compact text for the LLM prompt (~200 tokens for 5 posts)."""
        if not feed:
            return "Dein Feed ist leer — noch keine Posts vorhanden."

        lines = []
        for item in feed:
            age = current_round - item.created_round
            age_str = f"vor {age} Runde{'n' if age != 1 else ''}"
            tags = " ".join(f"#{t}" for t in item.hashtags[:3])
            engagement = f"{item.likes}L {item.comments}K {item.reposts}R"

            line = f"[{item.post_id}] @{item.author_id} ({age_str}): \"{item.content[:120]}\" | {engagement}"
            if tags:
                line += f" {tags}"
            lines.append(line)

        return "DEIN FEED:\n" + "\n".join(lines)

    async def execute_action(self, action: AgentAction) -> bool:
        """Execute an agent action and update the database."""
        action_type = action.action_type

        if action_type == "create_post":
            post_id = f"p-{uuid.uuid4().hex[:8]}"
            await self.db.insert_post(
                post_id=post_id,
                author_id=action.agent_id,
                content=action.content or "",
                created_round=action.round_number,
                hashtags=action.hashtags,
            )
            await self.db.log_action(
                action.round_number, action.agent_id, action_type,
                content=action.content, metadata={"post_id": post_id},
            )
            return True

        elif action_type == "like_post" and action.target_post_id:
            like_id = f"l-{uuid.uuid4().hex[:8]}"
            await self.db.insert_like(
                like_id, action.target_post_id, action.agent_id, action.round_number,
            )
            await self.db.log_action(
                action.round_number, action.agent_id, action_type,
                target_id=action.target_post_id,
            )
            return True

        elif action_type == "repost" and action.target_post_id:
            repost_id = f"r-{uuid.uuid4().hex[:8]}"
            await self.db.insert_repost(
                repost_id, action.target_post_id, action.agent_id, action.round_number,
            )
            await self.db.log_action(
                action.round_number, action.agent_id, action_type,
                target_id=action.target_post_id,
            )
            return True

        elif action_type == "comment" and action.target_post_id:
            comment_id = f"c-{uuid.uuid4().hex[:8]}"
            await self.db.insert_comment(
                comment_id, action.target_post_id, action.agent_id,
                action.content or "", action.round_number,
            )
            await self.db.log_action(
                action.round_number, action.agent_id, action_type,
                content=action.content, target_id=action.target_post_id,
            )
            return True

        elif action_type == "follow_user" and action.target_user_id:
            await self.db.insert_follow(
                action.agent_id, action.target_user_id, action.round_number,
            )
            self.graph.add_edge(action.agent_id, action.target_user_id)
            await self.db.log_action(
                action.round_number, action.agent_id, action_type,
                target_id=action.target_user_id,
            )
            return True

        elif action_type == "do_nothing":
            await self.db.log_action(
                action.round_number, action.agent_id, action_type,
            )
            return True

        return False

    def get_platform_rules_prompt(self) -> str:
        return (
            "PLATTFORM: Öffentliches Netzwerk (Twitter-ähnlich)\n"
            "REGELN:\n"
            "- Posts maximal 280 Zeichen\n"
            "- Hashtags erlaubt\n"
            "- Du kannst Posten, Liken, Retweeten, Kommentieren, Folgen oder Nichts tun\n"
            "- Wähle NUR eine Aktion pro Runde\n"
            "- Poste NUR wenn du wirklich etwas Relevantes zu sagen hast\n"
        )
