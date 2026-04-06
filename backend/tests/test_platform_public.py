"""Tests for the public network platform (Twitter-like)."""

import os
import tempfile

import pytest

from app.models.actions import AgentAction
from app.models.persona import AgentTier, BigFive, Persona
from app.models.simulation import PlatformType
from app.simulation.database import SimulationDB
from app.simulation.graph import SocialGraph
from app.simulation.platforms.public import PublicNetworkPlatform


def _make_persona(id: str, interests: list[str] | None = None) -> Persona:
    return Persona(
        id=id,
        name=f"Agent {id}",
        age=30,
        gender="female",
        country="CH",
        region="Zürich",
        occupation="Test",
        big_five=BigFive(openness=0.5, conscientiousness=0.5, extraversion=0.5,
                         agreeableness=0.5, neuroticism=0.5),
        interests=interests or [],
    )


@pytest.fixture
async def platform():
    """Create a platform with DB and graph."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = SimulationDB(db_path)
    await db.initialize()

    graph = SocialGraph(PlatformType.PUBLIC)
    personas = [_make_persona(f"u{i}") for i in range(10)]
    graph.initialize(personas, seed=42)

    # Insert users into DB
    for p in personas:
        await db.insert_user(p.id, p.name, "{}", "{}")

    plat = PublicNetworkPlatform(db, graph)

    yield plat, personas

    os.unlink(db_path)


class TestPublicNetworkPlatform:
    def test_platform_name(self):
        db = SimulationDB(":memory:")
        graph = SocialGraph(PlatformType.PUBLIC)
        platform = PublicNetworkPlatform(db, graph)
        assert platform.get_platform_name() == "Öffentliches Netzwerk"

    def test_action_types(self):
        db = SimulationDB(":memory:")
        graph = SocialGraph(PlatformType.PUBLIC)
        platform = PublicNetworkPlatform(db, graph)
        actions = platform.get_action_types()
        assert "create_post" in actions
        assert "like_post" in actions
        assert "do_nothing" in actions
        assert len(actions) == 6

    def test_tools_schema_valid(self):
        db = SimulationDB(":memory:")
        graph = SocialGraph(PlatformType.PUBLIC)
        platform = PublicNetworkPlatform(db, graph)
        tools = platform.get_tools_schema()
        assert len(tools) == 6
        for tool in tools:
            assert tool["type"] == "function"
            assert "name" in tool["function"]
            assert "parameters" in tool["function"]

    @pytest.mark.asyncio
    async def test_execute_create_post(self, platform):
        plat, personas = platform
        action = AgentAction(
            agent_id="u0",
            round_number=1,
            action_type="create_post",
            content="Hallo Welt!",
            hashtags=["test"],
        )
        result = await plat.execute_action(action)
        assert result is True

        # Verify post was created
        posts = await plat.db.get_posts_for_feed(max_round=1)
        assert len(posts) == 1
        assert posts[0]["content"] == "Hallo Welt!"

    @pytest.mark.asyncio
    async def test_execute_like_post(self, platform):
        plat, personas = platform
        # Create a post first
        await plat.db.insert_post("p1", "u0", "Test post", created_round=1)

        action = AgentAction(
            agent_id="u1",
            round_number=1,
            action_type="like_post",
            target_post_id="p1",
        )
        result = await plat.execute_action(action)
        assert result is True

    @pytest.mark.asyncio
    async def test_execute_comment(self, platform):
        plat, personas = platform
        await plat.db.insert_post("p1", "u0", "Test post", created_round=1)

        action = AgentAction(
            agent_id="u1",
            round_number=1,
            action_type="comment",
            target_post_id="p1",
            content="Guter Punkt!",
        )
        result = await plat.execute_action(action)
        assert result is True

    @pytest.mark.asyncio
    async def test_execute_follow(self, platform):
        plat, personas = platform
        action = AgentAction(
            agent_id="u0",
            round_number=1,
            action_type="follow_user",
            target_user_id="u5",
        )
        result = await plat.execute_action(action)
        assert result is True
        assert plat.graph.has_edge("u0", "u5")

    @pytest.mark.asyncio
    async def test_execute_do_nothing(self, platform):
        plat, personas = platform
        action = AgentAction(
            agent_id="u0",
            round_number=1,
            action_type="do_nothing",
        )
        result = await plat.execute_action(action)
        assert result is True

    @pytest.mark.asyncio
    async def test_generate_feed_empty(self, platform):
        plat, personas = platform
        feed = await plat.generate_feed("u0", personas[0], current_round=1)
        assert feed == []

    @pytest.mark.asyncio
    async def test_generate_feed_with_posts(self, platform):
        plat, personas = platform
        # Create some posts
        for i in range(10):
            await plat.db.insert_post(f"p{i}", f"u{i % 10}", f"Post {i}", created_round=1)

        feed = await plat.generate_feed("u0", personas[0], current_round=2, feed_size=5)
        assert len(feed) <= 5
        # Should not contain own posts
        assert all(item.author_id != "u0" for item in feed)

    @pytest.mark.asyncio
    async def test_format_feed_for_prompt(self, platform):
        plat, _ = platform
        feed = [
            _make_feed_item("p1", "u1", "Die Krise verschärft sich", round=1, likes=5, comments=2),
            _make_feed_item("p2", "u2", "Alles halb so wild", round=2, likes=1),
        ]
        text = plat.format_feed_for_prompt(feed, current_round=3)
        assert "DEIN FEED:" in text
        assert "Die Krise" in text
        assert "5L" in text

    @pytest.mark.asyncio
    async def test_format_empty_feed(self, platform):
        plat, _ = platform
        text = plat.format_feed_for_prompt([], current_round=1)
        assert "leer" in text.lower()

    def test_platform_rules_prompt(self):
        db = SimulationDB(":memory:")
        graph = SocialGraph(PlatformType.PUBLIC)
        platform = PublicNetworkPlatform(db, graph)
        rules = platform.get_platform_rules_prompt()
        assert "280 Zeichen" in rules
        assert "Öffentliches Netzwerk" in rules


def _make_feed_item(post_id, author_id, content, round=1, likes=0, comments=0):
    from app.models.actions import FeedItem
    return FeedItem(
        post_id=post_id,
        author_id=author_id,
        author_name=f"Agent {author_id}",
        content=content,
        created_round=round,
        likes=likes,
        comments=comments,
    )
