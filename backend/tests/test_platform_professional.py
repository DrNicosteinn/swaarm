"""Tests for the professional network platform (LinkedIn-like)."""

import os
import tempfile

import pytest

from app.models.actions import AgentAction
from app.models.persona import BigFive, Persona
from app.models.professional import ProfessionalProfile, SeniorityLevel
from app.models.simulation import PlatformType
from app.simulation.database import SimulationDB
from app.simulation.graph import SocialGraph
from app.simulation.platforms.professional import ProfessionalNetworkPlatform


def _make_pro_persona(id: str, interests: list[str] | None = None) -> Persona:
    return Persona(
        id=id,
        name=f"Agent {id}",
        age=35,
        gender="female",
        country="CH",
        region="Zürich",
        occupation="Manager",
        big_five=BigFive(
            openness=0.5, conscientiousness=0.6, extraversion=0.4,
            agreeableness=0.6, neuroticism=0.3,
        ),
        interests=interests or ["Leadership", "Innovation"],
        professional_profile=ProfessionalProfile(
            job_title="Head of Innovation",
            company_name="SwissCorp",
            seniority_level=SeniorityLevel.SENIOR,
            expertise_topics=["Innovation", "Digital Transformation"],
        ),
    )


@pytest.fixture
async def platform():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = SimulationDB(db_path)
    await db.initialize()

    graph = SocialGraph(PlatformType.PROFESSIONAL)
    personas = [_make_pro_persona(f"u{i}") for i in range(10)]
    graph.initialize(personas, seed=42)

    for p in personas:
        await db.insert_user(p.id, p.name, "{}", "{}")

    plat = ProfessionalNetworkPlatform(db, graph)
    yield plat, personas

    os.unlink(db_path)


class TestProfessionalPlatform:
    def test_platform_name(self):
        db = SimulationDB(":memory:")
        graph = SocialGraph(PlatformType.PROFESSIONAL)
        p = ProfessionalNetworkPlatform(db, graph)
        assert p.get_platform_name() == "Professionelles Netzwerk"

    def test_action_types(self):
        db = SimulationDB(":memory:")
        graph = SocialGraph(PlatformType.PROFESSIONAL)
        p = ProfessionalNetworkPlatform(db, graph)
        actions = p.get_action_types()
        assert "create_post" in actions
        assert "react_insightful" in actions
        assert "connect" in actions
        assert "do_nothing" in actions
        assert len(actions) == 13

    def test_tools_schema(self):
        db = SimulationDB(":memory:")
        graph = SocialGraph(PlatformType.PROFESSIONAL)
        p = ProfessionalNetworkPlatform(db, graph)
        tools = p.get_tools_schema()
        assert len(tools) == 7  # Consolidated tools (react has enum)
        names = [t["function"]["name"] for t in tools]
        assert "create_post" in names
        assert "react" in names
        assert "comment" in names
        assert "connect" in names
        assert "do_nothing" in names

    @pytest.mark.asyncio
    async def test_execute_create_post(self, platform):
        plat, _personas = platform
        action = AgentAction(
            agent_id="u0", round_number=1, action_type="create_post",
            content="Die Zukunft der digitalen Transformation liegt in der Zusammenarbeit.",
            hashtags=["DigitalTransformation"],
        )
        assert await plat.execute_action(action)

        posts = await plat.db.get_posts_for_feed(max_round=1)
        assert len(posts) == 1
        assert "Zusammenarbeit" in posts[0]["content"]

    @pytest.mark.asyncio
    async def test_execute_react_insightful(self, platform):
        plat, _personas = platform
        await plat.db.insert_post("p1", "u0", "Thought Leadership", created_round=1)

        action = AgentAction(
            agent_id="u1", round_number=1, action_type="react_insightful",
            target_post_id="p1",
        )
        assert await plat.execute_action(action)

    @pytest.mark.asyncio
    async def test_execute_react_via_react_action(self, platform):
        """Test the 'react' action type with reaction_type parameter."""
        plat, _personas = platform
        await plat.db.insert_post("p1", "u0", "Great content", created_round=1)

        action = AgentAction(
            agent_id="u1", round_number=1, action_type="react",
            target_post_id="p1", reaction_type="celebrate",
        )
        assert await plat.execute_action(action)

    @pytest.mark.asyncio
    async def test_execute_comment(self, platform):
        plat, _personas = platform
        await plat.db.insert_post("p1", "u0", "Original", created_round=1)

        action = AgentAction(
            agent_id="u1", round_number=1, action_type="comment",
            target_post_id="p1",
            content="Ein sehr guter Punkt. Die Transformation erfordert einen ganzheitlichen Ansatz.",
        )
        assert await plat.execute_action(action)

    @pytest.mark.asyncio
    async def test_execute_share(self, platform):
        plat, _personas = platform
        await plat.db.insert_post("p1", "u0", "Worth sharing", created_round=1)

        action = AgentAction(
            agent_id="u1", round_number=1, action_type="share",
            target_post_id="p1",
        )
        assert await plat.execute_action(action)

    @pytest.mark.asyncio
    async def test_execute_connect(self, platform):
        plat, _personas = platform
        action = AgentAction(
            agent_id="u0", round_number=1, action_type="connect",
            target_user_id="u9",
        )
        assert await plat.execute_action(action)
        # Undirected graph: both directions
        assert plat.graph.has_edge("u0", "u9")
        assert plat.graph.has_edge("u9", "u0")

    @pytest.mark.asyncio
    async def test_execute_do_nothing(self, platform):
        plat, _personas = platform
        action = AgentAction(agent_id="u0", round_number=1, action_type="do_nothing")
        assert await plat.execute_action(action)

    @pytest.mark.asyncio
    async def test_generate_feed_empty(self, platform):
        plat, personas = platform
        feed = await plat.generate_feed("u0", personas[0], current_round=1)
        assert feed == []

    @pytest.mark.asyncio
    async def test_generate_feed_with_posts(self, platform):
        plat, personas = platform
        for i in range(5):
            await plat.db.insert_post(f"p{i}", f"u{i}", f"Professional Post {i}", created_round=1)

        feed = await plat.generate_feed("u0", personas[0], current_round=2, feed_size=3)
        assert len(feed) <= 3
        assert all(item.author_id != "u0" for item in feed)

    @pytest.mark.asyncio
    async def test_format_feed_for_prompt(self, platform):
        plat, _ = platform
        from app.models.actions import FeedItem

        feed = [FeedItem(
            post_id="p1", author_id="u1", author_name="Lisa Hofer",
            content="Employer Branding ist entscheidend", created_round=1,
            likes=8, comments=3,
        )]
        text = plat.format_feed_for_prompt(feed, current_round=3)
        assert "DEIN FEED:" in text
        assert "Employer Branding" in text

    def test_platform_rules_prompt(self):
        db = SimulationDB(":memory:")
        graph = SocialGraph(PlatformType.PROFESSIONAL)
        p = ProfessionalNetworkPlatform(db, graph)
        rules = p.get_platform_rules_prompt()
        assert "3000 Zeichen" in rules
        assert "professionell" in rules.lower()
        assert "CHEF" in rules

    @pytest.mark.asyncio
    async def test_undirected_graph(self, platform):
        """Professional network uses undirected graph (bilateral connections)."""
        plat, _personas = platform
        assert not plat.graph.is_directed

    @pytest.mark.asyncio
    async def test_expertise_alignment_scoring(self, platform):
        plat, personas = platform
        # Post with matching hashtags should score higher
        matching_post = {
            "id": "p1", "author_id": "u1", "content": "Innovation",
            "created_round": 1, "likes": 5, "comments": 2, "reposts": 0,
            "hashtags": '["Innovation", "Digital"]', "content_format": "text",
            "has_external_link": 0, "has_media": 0, "sentiment": 0.0,
        }
        non_matching = {
            "id": "p2", "author_id": "u2", "content": "Cooking recipes",
            "created_round": 1, "likes": 5, "comments": 2, "reposts": 0,
            "hashtags": '["Cooking", "Food"]', "content_format": "text",
            "has_external_link": 0, "has_media": 0, "sentiment": 0.0,
        }
        connections = set(plat.graph.get_neighbors("u0"))
        score_match = plat._score_post(matching_post, "u0", personas[0], 2, connections)
        score_no = plat._score_post(non_matching, "u0", personas[0], 2, connections)
        assert score_match > score_no


class TestProfessionalProfile:
    def test_create_profile(self):
        profile = ProfessionalProfile(
            job_title="CTO",
            company_name="TechCorp",
            seniority_level=SeniorityLevel.C_LEVEL,
            expertise_topics=["AI", "Cloud"],
        )
        assert profile.seniority_level == SeniorityLevel.C_LEVEL

    def test_persona_with_profile(self):
        persona = _make_pro_persona("test-pro")
        assert persona.professional_profile is not None
        assert persona.professional_profile.job_title == "Head of Innovation"

    def test_persona_without_profile(self):
        persona = Persona(
            id="test-pub", name="Test", age=30, gender="male",
            country="DE", region="Berlin", occupation="Test",
            big_five=BigFive(openness=0.5, conscientiousness=0.5,
                             extraversion=0.5, agreeableness=0.5, neuroticism=0.5),
        )
        assert persona.professional_profile is None
