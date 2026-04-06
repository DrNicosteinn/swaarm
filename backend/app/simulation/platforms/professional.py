"""Professional network platform (LinkedIn-like).

Key differences from public network:
- Bilateral connections (undirected graph)
- 2nd-degree content visibility via connection engagement
- 6 reaction types (like, celebrate, insightful, support, love, funny)
- Professional tone enforcement
- Dwell-time-based scoring + expertise alignment
- Virality suppression
- Longer content (up to 3000 chars)
"""

import json
import math
import random
import uuid

from app.models.actions import AgentAction, FeedItem
from app.models.persona import Persona
from app.simulation.platforms.base import PlatformBase

ENGAGEMENT_WEIGHTS = {
    "react_like": 1.0,
    "react_celebrate": 2.0,
    "react_insightful": 3.0,
    "react_support": 1.5,
    "react_love": 1.5,
    "react_funny": 1.0,
    "comment": 8.0,
    "share": 6.0,
}

RECENCY_HALF_LIFE_ROUNDS = 5

FORMAT_MULTIPLIERS = {
    "text": 1.0,
    "image": 1.2,
    "carousel": 1.8,
    "article": 1.5,
    "video": 0.8,
    "link": 0.5,
}


class ProfessionalNetworkPlatform(PlatformBase):
    """LinkedIn-like professional network simulation."""

    def get_platform_name(self) -> str:
        return "Professionelles Netzwerk"

    def get_action_types(self) -> list[str]:
        return [
            "create_post", "create_article",
            "react_like", "react_celebrate", "react_insightful",
            "react_support", "react_love", "react_funny",
            "comment", "reply", "share", "connect", "do_nothing",
        ]

    def get_tools_schema(self) -> list[dict]:
        """OpenAI function calling tools for LinkedIn-like actions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_post",
                    "description": "Erstelle einen professionellen Post (max 3000 Zeichen).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "Der Posttext"},
                            "hashtags": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "create_article",
                    "description": "Schreibe einen ausführlichen Artikel (500-5000 Zeichen).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "title": {"type": "string"},
                        },
                        "required": ["content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "react",
                    "description": "Reagiere auf einen Post.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "post_id": {"type": "string"},
                            "reaction": {
                                "type": "string",
                                "enum": ["like", "celebrate", "insightful", "support", "love", "funny"],
                            },
                        },
                        "required": ["post_id", "reaction"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "comment",
                    "description": "Schreibe einen substanziellen Kommentar (2-5 Sätze).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "post_id": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["post_id", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "share",
                    "description": "Teile einen Post mit deinem Netzwerk.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "post_id": {"type": "string"},
                            "commentary": {
                                "type": "string",
                                "description": "Optionaler Kommentar",
                            },
                        },
                        "required": ["post_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "connect",
                    "description": "Sende eine Verbindungsanfrage.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string"},
                        },
                        "required": ["user_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "do_nothing",
                    "description": "Nichts tun — nur beobachten. Auf LinkedIn ist dies oft die klügste Wahl.",
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
        """3-source feed: direct connections + 2nd-degree engagement + discovery."""
        all_posts = await self.db.get_posts_for_feed(max_round=current_round, limit=200)
        if not all_posts:
            return []

        connections = set(self.graph.get_neighbors(agent_id))

        scored_posts: list[tuple[dict, float]] = []
        for post in all_posts:
            if post["author_id"] == agent_id:
                continue
            score = self._score_post(post, agent_id, agent_persona, current_round, connections)
            scored_posts.append((post, score))

        scored_posts.sort(key=lambda x: x[1], reverse=True)

        # 80% relevant + 20% discovery
        n_relevant = max(1, int(feed_size * 0.80))
        n_discovery = feed_size - n_relevant

        feed_posts = [p for p, _ in scored_posts[:n_relevant]]

        # Discovery: cross-community high-quality posts
        agent_community = self.graph.get_community(agent_id)
        tail = scored_posts[n_relevant:]
        cross = [p for p, _ in tail if self.graph.get_community(p["author_id"]) != agent_community]
        if len(cross) >= n_discovery:
            feed_posts.extend(random.sample(cross, n_discovery))
        elif tail:
            feed_posts.extend([p for p, _ in tail[:n_discovery]])

        return [self._to_feed_item(p) for p in feed_posts[:feed_size]]

    def _score_post(
        self, post: dict, viewer_id: str, viewer_persona: Persona,
        current_round: int, connections: set[str],
    ) -> float:
        """LinkedIn-style scoring with expertise alignment and dwell prediction."""
        # Engagement (log-dampened, heavier than Twitter)
        raw = (
            post.get("likes", 0) * ENGAGEMENT_WEIGHTS["react_like"]
            + post.get("comments", 0) * ENGAGEMENT_WEIGHTS["comment"]
            + post.get("reposts", 0) * ENGAGEMENT_WEIGHTS["share"]
        )
        engagement = 1.0 + math.log1p(math.sqrt(raw))  # Double-dampened for virality suppression

        # Recency (slower decay than Twitter)
        age = current_round - post.get("created_round", 0)
        recency = 2.0 ** (-age / RECENCY_HALF_LIFE_ROUNDS)

        # Professional proximity
        author_id = post["author_id"]
        if author_id in connections:
            proximity = 1.0
        elif self.graph.get_community(viewer_id) == self.graph.get_community(author_id):
            proximity = 0.25
        else:
            proximity = 0.08

        # Expertise alignment
        expertise = self._compute_expertise_alignment(viewer_persona, post)

        # Format modifier
        fmt = FORMAT_MULTIPLIERS.get(post.get("content_format", "text"), 1.0)

        # Link penalty
        link_penalty = 0.5 if post.get("has_external_link") else 1.0

        # Virality suppression (cap reach)
        total_engagement = post.get("likes", 0) + post.get("comments", 0)
        suppression = 1.0 / math.log2(max(total_engagement / 10, 2)) if total_engagement > 50 else 1.0

        return engagement * recency * proximity * expertise * fmt * link_penalty * suppression

    def _compute_expertise_alignment(self, viewer: Persona, post: dict) -> float:
        """How relevant is this post to the viewer's expertise?"""
        post_tags = set(json.loads(post.get("hashtags", "[]")))
        viewer_interests = set(viewer.interests)
        viewer_topics = set(viewer.posting_style.typical_topics)
        all_topics = viewer_interests | viewer_topics

        if viewer.professional_profile:
            all_topics.update(viewer.professional_profile.expertise_topics)

        if not post_tags and not all_topics:
            return 0.4

        if post_tags and all_topics:
            overlap = len(post_tags & all_topics)
            total = len(post_tags | all_topics)
            return 0.3 + 0.7 * (overlap / max(total, 1))

        return 0.4

    def _to_feed_item(self, post: dict) -> FeedItem:
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
        if not feed:
            return "Dein Feed ist leer — noch keine Posts vorhanden."

        lines = []
        for item in feed:
            age = current_round - item.created_round
            age_str = f"vor {age} Runde{'n' if age != 1 else ''}"
            tags = " ".join(f"#{t}" for t in item.hashtags[:3])
            engagement = f"{item.likes}R {item.comments}K"
            headline = f" | {item.author_headline}" if item.author_headline else ""

            line = (
                f"[{item.post_id}] @{item.author_id}{headline} ({age_str}): "
                f'"{item.content[:200]}" | {engagement}'
            )
            if tags:
                line += f" {tags}"
            lines.append(line)

        return "DEIN FEED:\n" + "\n".join(lines)

    async def execute_action(self, action: AgentAction) -> bool:
        at = action.action_type

        if at in ("create_post", "create_article"):
            post_id = f"p-{uuid.uuid4().hex[:8]}"
            content = (action.content or "")[:3000]  # LinkedIn limit
            await self.db.insert_post(
                post_id=post_id, author_id=action.agent_id,
                content=content, created_round=action.round_number,
                hashtags=action.hashtags,
                content_format="article" if at == "create_article" else "text",
            )
            await self.db.log_action(
                action.round_number, action.agent_id, at,
                content=content, metadata={"post_id": post_id},
            )
            return True

        if at.startswith("react_") and action.target_post_id:
            reaction = at.replace("react_", "")
            like_id = f"l-{uuid.uuid4().hex[:8]}"
            await self.db.insert_like(
                like_id, action.target_post_id, action.agent_id,
                action.round_number, reaction_type=reaction,
            )
            await self.db.log_action(
                action.round_number, action.agent_id, at,
                target_id=action.target_post_id,
                metadata={"reaction": reaction},
            )
            return True

        if at == "comment" and action.target_post_id:
            comment_id = f"c-{uuid.uuid4().hex[:8]}"
            await self.db.insert_comment(
                comment_id, action.target_post_id, action.agent_id,
                action.content or "", action.round_number,
            )
            await self.db.log_action(
                action.round_number, action.agent_id, at,
                content=action.content, target_id=action.target_post_id,
            )
            return True

        if at == "share" and action.target_post_id:
            repost_id = f"s-{uuid.uuid4().hex[:8]}"
            await self.db.insert_repost(
                repost_id, action.target_post_id, action.agent_id,
                action.round_number,
            )
            await self.db.log_action(
                action.round_number, action.agent_id, at,
                target_id=action.target_post_id,
            )
            return True

        if at == "connect" and action.target_user_id:
            self.graph.add_edge(action.agent_id, action.target_user_id)
            await self.db.insert_follow(
                action.agent_id, action.target_user_id, action.round_number,
            )
            await self.db.log_action(
                action.round_number, action.agent_id, at,
                target_id=action.target_user_id,
            )
            return True

        if at == "do_nothing":
            await self.db.log_action(action.round_number, action.agent_id, at)
            return True

        # Handle "react" action (from LLM tool call with reaction parameter)
        if at == "react" and action.target_post_id:
            reaction = action.reaction_type or "like"
            like_id = f"l-{uuid.uuid4().hex[:8]}"
            await self.db.insert_like(
                like_id, action.target_post_id, action.agent_id,
                action.round_number, reaction_type=reaction,
            )
            await self.db.log_action(
                action.round_number, action.agent_id, f"react_{reaction}",
                target_id=action.target_post_id,
            )
            return True

        return False

    def get_platform_rules_prompt(self) -> str:
        return (
            "PLATTFORM: Professionelles Netzwerk (LinkedIn-ähnlich)\n"
            "REGELN:\n"
            "- Posts maximal 3000 Zeichen, bevorzuge 500-1500\n"
            "- Dein CHEF, KUNDEN und RECRUITER sehen alles\n"
            "- Professioneller Ton — keine Beleidigungen, kein Sarkasmus\n"
            "- Kommentare substanziell (2-5 Sätze), nicht 'Toller Beitrag!'\n"
            "- Reaktionen: like, celebrate, insightful, support, love, funny\n"
            "- Wähle NUR eine Aktion pro Runde\n"
            "- Poste NUR wenn es deiner professionellen Marke dient\n"
            "- do_nothing ist oft die klügste Aktion\n"
        )
