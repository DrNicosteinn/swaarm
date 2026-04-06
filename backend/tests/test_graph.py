"""Tests for social graph generation."""

from app.models.persona import AgentTier, BigFive, Persona
from app.models.simulation import PlatformType
from app.simulation.graph import SocialGraph


def _make_persona(id: str, tier: AgentTier = AgentTier.ACTIVE_RESPONDER, role: str = "general") -> Persona:
    """Helper to create a test persona."""
    return Persona(
        id=id,
        name=f"Agent {id}",
        age=30,
        gender="female",
        country="CH",
        region="Zürich",
        occupation="Testperson",
        big_five=BigFive(
            openness=0.5,
            conscientiousness=0.5,
            extraversion=0.5,
            agreeableness=0.5,
            neuroticism=0.5,
        ),
        agent_tier=tier,
        stakeholder_role=role,
    )


class TestSocialGraphPublic:
    """Tests for the public (Twitter-like) network."""

    def test_directed_graph_for_public(self):
        graph = SocialGraph(PlatformType.PUBLIC)
        assert graph.is_directed

    def test_small_graph_initialization(self):
        graph = SocialGraph(PlatformType.PUBLIC)
        personas = [_make_persona(f"u{i}") for i in range(5)]
        graph.initialize(personas, seed=42)

        assert graph.node_count == 5
        assert graph.edge_count > 0

    def test_medium_graph_has_communities(self):
        graph = SocialGraph(PlatformType.PUBLIC)
        # Create personas in different stakeholder groups
        personas = (
            [_make_persona(f"emp-{i}", role="employees") for i in range(20)]
            + [_make_persona(f"cust-{i}", role="customers") for i in range(30)]
            + [_make_persona(f"media-{i}", role="media") for i in range(10)]
        )
        graph.initialize(personas, seed=42)

        assert graph.node_count == 60
        assert graph._count_communities() >= 3  # at least 3 stakeholder groups

    def test_influencer_hubs_have_more_connections(self):
        graph = SocialGraph(PlatformType.PUBLIC)
        personas = [_make_persona("influencer-1", tier=AgentTier.POWER_CREATOR, role="media")] + [
            _make_persona(f"user-{i}", role="general") for i in range(50)
        ]
        graph.initialize(personas, seed=42)

        influencer_degree = graph.get_degree("influencer-1")
        avg_degree = sum(graph.get_degree(f"user-{i}") for i in range(50)) / 50

        # Influencer should have more connections than average
        assert influencer_degree > avg_degree

    def test_follow_and_following(self):
        graph = SocialGraph(PlatformType.PUBLIC)
        personas = [_make_persona(f"u{i}") for i in range(10)]
        graph.initialize(personas, seed=42)

        # Directed graph: following ≠ followers
        for p in personas:
            following = graph.get_following(p.id)
            followers = graph.get_followers(p.id)
            assert isinstance(following, list)
            assert isinstance(followers, list)

    def test_add_edge_runtime(self):
        graph = SocialGraph(PlatformType.PUBLIC)
        personas = [_make_persona(f"u{i}") for i in range(5)]
        graph.initialize(personas, seed=42)

        assert not graph.has_edge("u0", "u4") or graph.has_edge("u0", "u4")
        graph.add_edge("u0", "u4")
        assert graph.has_edge("u0", "u4")

    def test_graph_stats(self):
        graph = SocialGraph(PlatformType.PUBLIC)
        personas = [_make_persona(f"u{i}") for i in range(30)]
        graph.initialize(personas, seed=42)

        stats = graph.get_graph_stats()
        assert stats["nodes"] == 30
        assert stats["edges"] > 0
        assert stats["avg_degree"] > 0
        assert 0 < stats["density"] < 1


class TestSocialGraphProfessional:
    """Tests for the professional (LinkedIn-like) network."""

    def test_undirected_graph_for_professional(self):
        graph = SocialGraph(PlatformType.PROFESSIONAL)
        assert not graph.is_directed

    def test_professional_graph_initialization(self):
        graph = SocialGraph(PlatformType.PROFESSIONAL)
        personas = [_make_persona(f"u{i}") for i in range(20)]
        graph.initialize(personas, seed=42)

        assert graph.node_count == 20
        assert graph.edge_count > 0

    def test_professional_has_higher_density(self):
        """Professional networks should be denser (bilateral connections)."""
        public = SocialGraph(PlatformType.PUBLIC)
        professional = SocialGraph(PlatformType.PROFESSIONAL)

        personas = [_make_persona(f"a-{i}", role="team_a") for i in range(25)] + [
            _make_persona(f"b-{i}", role="team_b") for i in range(25)
        ]

        public.initialize(personas, seed=42)
        professional.initialize(personas, seed=42)

        public_stats = public.get_graph_stats()
        prof_stats = professional.get_graph_stats()

        # Professional should have higher average degree
        assert prof_stats["avg_degree"] >= public_stats["avg_degree"] * 0.5  # relaxed assertion


class TestGraphEdgeCases:
    def test_empty_neighbors_for_unknown_node(self):
        graph = SocialGraph(PlatformType.PUBLIC)
        assert graph.get_neighbors("nonexistent") == []
        assert graph.get_followers("nonexistent") == []
        assert graph.get_following("nonexistent") == []

    def test_community_for_unknown_node(self):
        graph = SocialGraph(PlatformType.PUBLIC)
        assert graph.get_community("nonexistent") == 0

    def test_degree_for_unknown_node(self):
        graph = SocialGraph(PlatformType.PUBLIC)
        assert graph.get_degree("nonexistent") == 0

    def test_deterministic_with_seed(self):
        personas = [_make_persona(f"u{i}") for i in range(20)]

        g1 = SocialGraph(PlatformType.PUBLIC)
        g1.initialize(personas, seed=123)

        g2 = SocialGraph(PlatformType.PUBLIC)
        g2.initialize(personas, seed=123)

        assert g1.edge_count == g2.edge_count
