"""Tests for checkpoint save/load system."""

import os
import tempfile

import pytest

from app.models.agent import AgentState
from app.simulation.checkpoint import CheckpointData, CheckpointManager
from app.simulation.database import SimulationDB


@pytest.fixture
async def checkpoint_setup():
    """Create a DB with checkpoint table."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = SimulationDB(db_path)
    await db.initialize()

    mgr = CheckpointManager(db_path, interval=5)
    yield mgr, db_path

    os.unlink(db_path)


class TestCheckpointManager:
    @pytest.mark.asyncio
    async def test_should_checkpoint(self, checkpoint_setup):
        mgr, _ = checkpoint_setup
        assert not mgr.should_checkpoint(1)
        assert not mgr.should_checkpoint(3)
        assert mgr.should_checkpoint(5)
        assert mgr.should_checkpoint(10)

    @pytest.mark.asyncio
    async def test_save_and_load(self, checkpoint_setup):
        mgr, _ = checkpoint_setup

        checkpoint = CheckpointData(
            simulation_id="sim-001",
            round_number=5,
            agent_states={"agent-1": {"persona_id": "agent-1", "posts_created": 3}},
            last_active_rounds=[1, 2, 3],
            total_cost_usd=0.05,
        )

        await mgr.save(checkpoint)
        loaded = await mgr.load_latest()

        assert loaded is not None
        assert loaded.round_number == 5
        assert loaded.simulation_id == "sim-001"
        assert loaded.total_cost_usd == 0.05
        assert "agent-1" in loaded.agent_states

    @pytest.mark.asyncio
    async def test_load_empty(self, checkpoint_setup):
        mgr, _ = checkpoint_setup
        loaded = await mgr.load_latest()
        assert loaded is None

    @pytest.mark.asyncio
    async def test_keeps_only_last_3(self, checkpoint_setup):
        mgr, _ = checkpoint_setup

        for i in range(1, 7):
            cp = CheckpointData(
                simulation_id="sim-001",
                round_number=i * 5,
                total_cost_usd=i * 0.01,
            )
            await mgr.save(cp)

        count = await mgr.get_checkpoint_count()
        assert count == 3

        # Latest should be round 30
        latest = await mgr.load_latest()
        assert latest is not None
        assert latest.round_number == 30

    @pytest.mark.asyncio
    async def test_overwrite_same_round(self, checkpoint_setup):
        mgr, _ = checkpoint_setup

        cp1 = CheckpointData(simulation_id="sim-001", round_number=5, total_cost_usd=0.01)
        await mgr.save(cp1)

        cp2 = CheckpointData(simulation_id="sim-001", round_number=5, total_cost_usd=0.05)
        await mgr.save(cp2)

        loaded = await mgr.load_latest()
        assert loaded is not None
        assert loaded.total_cost_usd == 0.05  # Updated value

    @pytest.mark.asyncio
    async def test_create_checkpoint_from_state(self, checkpoint_setup):
        states = {
            "a1": AgentState(persona_id="a1", posts_created=5),
            "a2": AgentState(persona_id="a2", likes_given=10),
        }

        cp = CheckpointManager.create_checkpoint(
            simulation_id="sim-001",
            round_number=10,
            agent_states=states,
            last_active_rounds=[8, 9],
            total_cost_usd=0.15,
        )

        assert cp.round_number == 10
        assert len(cp.agent_states) == 2
        assert cp.agent_states["a1"]["posts_created"] == 5
