"""Tests for agent memory system."""

from app.models.agent import AgentState
from app.simulation.memory import MemoryManager


class TestMemoryManager:
    def setup_method(self):
        self.mm = MemoryManager(llm=None)  # No LLM for unit tests
        self.state = AgentState(persona_id="test-agent")

    def test_record_observation(self):
        self.mm.record_observation(self.state, "Sah einen Post über Entlassungen")
        assert len(self.state.memory.recent_observations) == 1

    def test_record_important_memory(self):
        self.mm.record_observation(
            self.state, "Mein Post bekam 50 Likes!", importance=8.0
        )
        assert len(self.state.memory.important_memories) == 1
        assert len(self.state.memory.recent_observations) == 1

    def test_low_importance_not_stored(self):
        self.mm.record_observation(
            self.state, "Scrollte durch den Feed", importance=2.0
        )
        assert len(self.state.memory.important_memories) == 0
        assert len(self.state.memory.recent_observations) == 1

    def test_build_memory_prompt_empty(self):
        prompt = self.mm.build_memory_prompt(self.state)
        assert "keine erinnerungen" in prompt.lower()

    def test_build_memory_prompt_with_observations(self):
        self.mm.record_observation(self.state, "Sah einen kritischen Post")
        self.mm.record_observation(self.state, "Diskussion wurde hitzig")
        prompt = self.mm.build_memory_prompt(self.state)
        assert "LETZTE BEOBACHTUNGEN" in prompt
        assert "kritischen Post" in prompt

    def test_build_memory_prompt_with_important(self):
        self.mm.record_observation(
            self.state, "Mein Post ging viral!", importance=9.0
        )
        prompt = self.mm.build_memory_prompt(self.state)
        assert "WICHTIGE ERINNERUNGEN" in prompt
        assert "viral" in prompt

    def test_build_memory_prompt_with_summary(self):
        self.state.memory.memory_summary = "Bisherige Diskussion war kontrovers."
        prompt = self.mm.build_memory_prompt(self.state)
        assert "ZUSAMMENFASSUNG" in prompt
        assert "kontrovers" in prompt

    def test_prompt_limits_observations(self):
        """Prompt should include max 3 recent observations even if more exist."""
        for i in range(7):
            self.mm.record_observation(self.state, f"Beobachtung {i}")
        prompt = self.mm.build_memory_prompt(self.state)
        # Sliding window keeps 5, but prompt shows max 3
        assert prompt.count("Beobachtung") == 3


class TestObservationText:
    def test_create_post(self):
        text = MemoryManager.compute_observation_text(
            "create_post", content="Die Krise verschärft sich"
        )
        assert "Post erstellt" in text
        assert "Krise" in text

    def test_create_post_with_engagement(self):
        text = MemoryManager.compute_observation_text(
            "create_post", content="Test", engagement=15
        )
        assert "15 Reaktionen" in text

    def test_like(self):
        text = MemoryManager.compute_observation_text(
            "like_post", target_info="@MaxMueller"
        )
        assert "MaxMueller" in text
        assert "geliked" in text

    def test_do_nothing(self):
        text = MemoryManager.compute_observation_text("do_nothing")
        assert "beobachtet" in text

    def test_comment(self):
        text = MemoryManager.compute_observation_text(
            "comment", content="Stimmt nicht ganz"
        )
        assert "Kommentar" in text


class TestImportanceScoring:
    def test_create_post_base(self):
        score = MemoryManager.compute_importance("create_post")
        assert score == 4.0

    def test_do_nothing_zero(self):
        score = MemoryManager.compute_importance("do_nothing")
        assert score == 0.0

    def test_high_engagement_boost(self):
        score = MemoryManager.compute_importance("create_post", engagement_received=20)
        assert score >= 7.0

    def test_controversial_boost(self):
        score = MemoryManager.compute_importance("comment", is_controversial=True)
        assert score >= 5.0

    def test_max_cap(self):
        score = MemoryManager.compute_importance(
            "create_post", engagement_received=100, is_controversial=True
        )
        assert score >= 9.0  # Capped at 10, but base 4 + 3 (engagement) + 2 (controversial) = 9
