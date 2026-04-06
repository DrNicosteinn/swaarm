"""Social graph generation and management using networkx.

Generates realistic social network graphs with:
- Power-law degree distribution (few influencers, many normal users)
- Community structure (interest-based clusters)
- Weak ties between communities (Granovetter bridges)
"""

import random

import networkx as nx
from loguru import logger

from app.models.persona import AgentTier, Persona
from app.models.simulation import PlatformType

# LFR-inspired parameters per platform
GRAPH_PARAMS = {
    PlatformType.PUBLIC: {
        "tau1": 2.1,  # degree distribution exponent
        "tau2": 1.5,  # community size exponent
        "mu": 0.15,  # mixing parameter (lower = stronger communities)
        "average_degree_ratio": 0.008,  # avg_degree as fraction of total nodes
        "min_degree": 2,
        "min_community_ratio": 0.02,  # minimum community as fraction of nodes
    },
    PlatformType.PROFESSIONAL: {
        "tau1": 2.7,  # less extreme power-law for professional
        "tau2": 1.5,
        "mu": 0.25,  # more cross-community mixing
        "average_degree_ratio": 0.012,
        "min_degree": 3,
        "min_community_ratio": 0.03,
    },
}


class SocialGraph:
    """Manages the social network graph for a simulation."""

    def __init__(self, platform: PlatformType):
        self.platform = platform
        self.is_directed = platform == PlatformType.PUBLIC
        self.graph: nx.Graph | nx.DiGraph = nx.DiGraph() if self.is_directed else nx.Graph()

    @property
    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def initialize(
        self,
        personas: list[Persona],
        seed: int | None = None,
    ) -> None:
        """Generate a realistic social graph from personas.

        Uses community-aware generation with power-law degree distribution.
        """
        rng = random.Random(seed)
        n = len(personas)

        if n < 10:
            self._build_simple_graph(personas, rng)
            return

        # Build graph with community structure
        self._build_community_graph(personas, rng)

        # Add influencer hubs (power creators get extra connections)
        self._add_influencer_hubs(personas, rng)

        # Add weak ties between communities
        self._add_weak_ties(rng)

        logger.info(
            f"Social graph initialized: {self.node_count} nodes, "
            f"{self.edge_count} edges, "
            f"communities: {self._count_communities()}"
        )

    def _build_simple_graph(self, personas: list[Persona], rng: random.Random) -> None:
        """Build a simple graph for small simulations (<10 agents)."""
        for persona in personas:
            self.graph.add_node(persona.id, community=0)

        ids = [p.id for p in personas]
        for _i, p in enumerate(personas):
            # Each agent connects to 2-3 random others
            n_connections = min(rng.randint(2, 3), len(ids) - 1)
            targets = [t for t in ids if t != p.id]
            rng.shuffle(targets)
            for target in targets[:n_connections]:
                self.graph.add_edge(p.id, target)

    def _build_community_graph(self, personas: list[Persona], rng: random.Random) -> None:
        """Build graph with community structure based on stakeholder roles."""
        len(personas)

        # Group personas by stakeholder role (= communities)
        communities: dict[str, list[Persona]] = {}
        for p in personas:
            role = p.stakeholder_role or "general"
            communities.setdefault(role, []).append(p)

        # Add all nodes with community labels
        for community_idx, (role, members) in enumerate(communities.items()):
            for p in members:
                self.graph.add_node(p.id, community=community_idx, role=role)

        # Intra-community edges (dense connections within groups)
        params = GRAPH_PARAMS[self.platform]
        for _role, members in communities.items():
            member_ids = [p.id for p in members]
            n_members = len(member_ids)
            if n_members < 2:
                continue

            # Each member connects to ~30-50% of their community
            for p_id in member_ids:
                n_connections = max(1, int(n_members * rng.uniform(0.15, 0.35)))
                targets = [t for t in member_ids if t != p_id]
                rng.shuffle(targets)
                for target in targets[:n_connections]:
                    self.graph.add_edge(p_id, target)

        # Inter-community edges (~5-10% of total edges)
        all_ids = [p.id for p in personas]
        n_inter = max(1, int(self.edge_count * params["mu"]))
        for _ in range(n_inter):
            a, b = rng.sample(all_ids, 2)
            if self.graph.nodes[a].get("community") != self.graph.nodes[b].get("community"):
                self.graph.add_edge(a, b)

    def _add_influencer_hubs(self, personas: list[Persona], rng: random.Random) -> None:
        """Give power creators extra cross-community connections."""
        creators = [p for p in personas if p.agent_tier == AgentTier.POWER_CREATOR]
        all_ids = [p.id for p in personas]

        for creator in creators:
            # Influencers get 3-5x more connections than average
            n_extra = max(3, int(len(all_ids) * 0.02))
            targets = [
                t for t in all_ids if t != creator.id and not self.graph.has_edge(creator.id, t)
            ]
            rng.shuffle(targets)
            for target in targets[:n_extra]:
                self.graph.add_edge(creator.id, target)
                # For directed graphs, also add reverse follows (people follow influencers)
                if self.is_directed:
                    self.graph.add_edge(target, creator.id)

    def _add_weak_ties(self, rng: random.Random) -> None:
        """Add Granovetter-style bridge edges between communities."""
        communities = {}
        for node, data in self.graph.nodes(data=True):
            c = data.get("community", 0)
            communities.setdefault(c, []).append(node)

        community_list = list(communities.values())
        if len(community_list) < 2:
            return

        # Add ~5% weak ties
        n_weak = max(1, int(self.edge_count * 0.05))
        for _ in range(n_weak):
            c1, c2 = rng.sample(community_list, 2)
            if c1 and c2:
                a = rng.choice(c1)
                b = rng.choice(c2)
                self.graph.add_edge(a, b)

    def _count_communities(self) -> int:
        """Count unique communities in the graph."""
        communities = {data.get("community", 0) for _, data in self.graph.nodes(data=True)}
        return len(communities)

    def get_neighbors(self, node_id: str) -> list[str]:
        """Get all neighbors (followers/connections) of a node."""
        if node_id not in self.graph:
            return []
        return list(self.graph.neighbors(node_id))

    def get_followers(self, node_id: str) -> list[str]:
        """Get followers of a node (predecessors in directed graph)."""
        if self.is_directed and node_id in self.graph:
            return list(self.graph.predecessors(node_id))
        return self.get_neighbors(node_id)

    def get_following(self, node_id: str) -> list[str]:
        """Get who this node follows (successors in directed graph)."""
        if self.is_directed and node_id in self.graph:
            return list(self.graph.successors(node_id))
        return self.get_neighbors(node_id)

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Add a new follow/connection edge."""
        self.graph.add_edge(from_id, to_id)

    def has_edge(self, from_id: str, to_id: str) -> bool:
        """Check if an edge exists."""
        return self.graph.has_edge(from_id, to_id)

    def get_community(self, node_id: str) -> int:
        """Get the community label of a node."""
        if node_id in self.graph:
            return self.graph.nodes[node_id].get("community", 0)
        return 0

    def get_degree(self, node_id: str) -> int:
        """Get the degree (number of connections) of a node."""
        if node_id in self.graph:
            return self.graph.degree(node_id)
        return 0

    def get_graph_stats(self) -> dict:
        """Get basic graph statistics."""
        g = self.graph.to_undirected() if self.is_directed else self.graph
        return {
            "nodes": self.node_count,
            "edges": self.edge_count,
            "communities": self._count_communities(),
            "avg_degree": sum(dict(g.degree()).values()) / max(self.node_count, 1),
            "density": nx.density(g),
        }
