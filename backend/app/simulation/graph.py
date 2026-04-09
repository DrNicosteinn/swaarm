"""Social graph generation and management using networkx.

Generates realistic social network graphs with:
- Sparse, meaningful connections (avg 2-4 per agent)
- Hub-spoke structure within communities (few connectors, many leaf nodes)
- Community structure based on stakeholder roles
- Sparse bridges between communities (information flow paths)

Design principles (based on MiroFish/OASIS research):
- Every edge should represent a plausible relationship
- Max 2-3 edges for regular agents, 4-8 for hubs
- Clear visual cluster separation with few cross-cluster bridges
- Power-law degree distribution emerges from hub assignment, not random wiring
"""

import random

import networkx as nx
from loguru import logger

from app.models.persona import AgentTier, Persona
from app.models.simulation import PlatformType

# Platform-specific parameters
GRAPH_PARAMS = {
    PlatformType.PUBLIC: {
        "intra_hub_connections": 3,  # hub connects to N peers in its community
        "intra_leaf_connections": 1,  # leaf connects to N peers (beyond hub)
        "inter_bridge_ratio": 0.08,  # 8% of nodes get a cross-community bridge
        "influencer_extra": 3,  # extra connections for power_creators
        "min_degree": 1,
    },
    PlatformType.PROFESSIONAL: {
        "intra_hub_connections": 4,
        "intra_leaf_connections": 2,
        "inter_bridge_ratio": 0.12,  # more mixing in professional networks
        "influencer_extra": 4,
        "min_degree": 2,
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
        """Generate a sparse, meaningful social graph from personas.

        Architecture:
        1. Group personas by stakeholder_role → communities
        2. Within each community: pick 1-2 hubs, connect others to hubs (star topology)
        3. Add sparse peer connections within communities
        4. Add sparse bridges between communities
        5. Boost power_creator degree
        """
        rng = random.Random(seed)
        n = len(personas)

        if n < 10:
            self._build_simple_graph(personas, rng)
            return

        self._build_sparse_graph(personas, rng)

        stats = self.get_graph_stats()
        logger.info(
            f"Social graph initialized: {stats['nodes']} nodes, "
            f"{stats['edges']} edges, "
            f"avg_degree={stats['avg_degree']:.1f}, "
            f"communities={stats['communities']}"
        )

    def _build_simple_graph(self, personas: list[Persona], rng: random.Random) -> None:
        """Build a simple graph for small simulations (<10 agents)."""
        for persona in personas:
            self.graph.add_node(persona.id, community=0, role=persona.stakeholder_role or "general")

        ids = [p.id for p in personas]
        for p in personas:
            n_connections = min(rng.randint(1, 2), len(ids) - 1)
            targets = [t for t in ids if t != p.id]
            rng.shuffle(targets)
            for target in targets[:n_connections]:
                self.graph.add_edge(p.id, target)

    def _build_sparse_graph(self, personas: list[Persona], rng: random.Random) -> None:
        """Build sparse hub-spoke graph with meaningful structure."""
        params = GRAPH_PARAMS[self.platform]

        # Step 1: Group by stakeholder role → communities
        communities: dict[str, list[Persona]] = {}
        for p in personas:
            role = p.stakeholder_role or "general"
            communities.setdefault(role, []).append(p)

        # Add all nodes
        for community_idx, (role, members) in enumerate(communities.items()):
            for p in members:
                self.graph.add_node(p.id, community=community_idx, role=role)

        # Step 2: Within each community, build hub-spoke structure
        community_hubs: dict[int, list[str]] = {}
        for community_idx, (role, members) in enumerate(communities.items()):
            if len(members) < 2:
                continue

            # Pick 1-2 hubs per community (prefer power_creators and active_responders)
            sorted_members = sorted(
                members,
                key=lambda p: (
                    0
                    if p.agent_tier == AgentTier.POWER_CREATOR
                    else 1
                    if p.agent_tier == AgentTier.ACTIVE_RESPONDER
                    else 2
                ),
            )
            n_hubs = max(1, min(3, len(members) // 8))
            hubs = sorted_members[:n_hubs]
            leaves = sorted_members[n_hubs:]
            community_hubs[community_idx] = [h.id for h in hubs]

            # Connect every leaf to exactly one hub (star topology)
            for leaf in leaves:
                hub = rng.choice(hubs)
                self.graph.add_edge(leaf.id, hub.id)

            # Hub-to-hub connections (if multiple hubs)
            for i in range(len(hubs)):
                for j in range(i + 1, len(hubs)):
                    self.graph.add_edge(hubs[i].id, hubs[j].id)

            # Sparse peer connections: some leaves connect to 1 other leaf
            member_ids = [p.id for p in members]
            n_peer = max(0, int(len(leaves) * 0.3))
            peer_candidates = [l.id for l in leaves]
            rng.shuffle(peer_candidates)
            for k in range(0, min(n_peer * 2, len(peer_candidates) - 1), 2):
                self.graph.add_edge(peer_candidates[k], peer_candidates[k + 1])

        # Step 3: Sparse bridges between communities
        community_ids = list(community_hubs.keys())
        if len(community_ids) >= 2:
            # Connect community hubs to hubs of other communities
            for ci in community_ids:
                # Each community gets 1-2 bridges to other communities
                other_communities = [c for c in community_ids if c != ci]
                n_bridges = min(len(other_communities), rng.randint(1, 2))
                bridge_targets = rng.sample(other_communities, n_bridges)
                for cj in bridge_targets:
                    hub_a = rng.choice(community_hubs[ci])
                    hub_b = rng.choice(community_hubs[cj])
                    if not self.graph.has_edge(hub_a, hub_b):
                        self.graph.add_edge(hub_a, hub_b)

            # A few random cross-community bridges for non-hubs
            all_ids = [p.id for p in personas]
            n_random_bridges = max(1, int(len(all_ids) * params["inter_bridge_ratio"]))
            for _ in range(n_random_bridges):
                a, b = rng.sample(all_ids, 2)
                if self.graph.nodes[a].get("community") != self.graph.nodes[b].get(
                    "community"
                ) and not self.graph.has_edge(a, b):
                    self.graph.add_edge(a, b)

        # Step 4: Boost power_creators with extra connections
        creators = [p for p in personas if p.agent_tier == AgentTier.POWER_CREATOR]
        all_ids = [p.id for p in personas]
        for creator in creators:
            current_degree = self.graph.degree(creator.id)
            n_extra = max(0, params["influencer_extra"] - current_degree + 2)
            targets = [t for t in all_ids if t != creator.id and not self.graph.has_edge(creator.id, t)]
            rng.shuffle(targets)
            for target in targets[:n_extra]:
                self.graph.add_edge(creator.id, target)
                if self.is_directed:
                    self.graph.add_edge(target, creator.id)

        # Step 5: Ensure minimum degree
        min_degree = params["min_degree"]
        for p in personas:
            degree = self.graph.degree(p.id)
            if degree < min_degree:
                targets = [t for t in all_ids if t != p.id and not self.graph.has_edge(p.id, t)]
                if targets:
                    rng.shuffle(targets)
                    for target in targets[: min_degree - degree]:
                        self.graph.add_edge(p.id, target)

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
