"""Checkpoint system — save and restore simulation state for crash recovery.

Saves state every N rounds. On crash, simulation resumes from last checkpoint.
Keeps last 3 checkpoints to limit disk usage.
"""

import json
import time

import aiosqlite
from loguru import logger
from pydantic import BaseModel, Field

from app.models.agent import AgentState


class CheckpointData(BaseModel):
    """Complete simulation state at a checkpoint."""

    simulation_id: str
    round_number: int
    agent_states: dict[str, dict] = Field(default_factory=dict)  # agent_id → state dict
    last_active_rounds: list[int] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    created_at: float = Field(default_factory=time.time)


class CheckpointManager:
    """Manages simulation checkpoints in the SQLite database."""

    def __init__(self, db_path: str, interval: int = 5):
        self.db_path = db_path
        self.interval = interval

    def should_checkpoint(self, round_number: int) -> bool:
        """Check if we should save a checkpoint at this round."""
        return round_number % self.interval == 0

    async def save(self, checkpoint: CheckpointData) -> None:
        """Save a checkpoint to the simulation database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO checkpoints (round_number, state_json, created_at) VALUES (?, ?, ?)",
                (checkpoint.round_number, checkpoint.model_dump_json(), checkpoint.created_at),
            )
            # Keep only last 3 checkpoints
            await db.execute(
                "DELETE FROM checkpoints WHERE round_number NOT IN "
                "(SELECT round_number FROM checkpoints ORDER BY round_number DESC LIMIT 3)"
            )
            await db.commit()

        logger.info(f"Checkpoint saved at round {checkpoint.round_number}")

    async def load_latest(self) -> CheckpointData | None:
        """Load the most recent checkpoint, if any."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT state_json FROM checkpoints ORDER BY round_number DESC LIMIT 1"
            )
            row = await cursor.fetchone()

        if row:
            data = CheckpointData.model_validate_json(row[0])
            logger.info(f"Checkpoint loaded from round {data.round_number}")
            return data

        return None

    async def get_checkpoint_count(self) -> int:
        """Get number of saved checkpoints."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM checkpoints")
            row = await cursor.fetchone()
            return row[0] if row else 0

    @staticmethod
    def create_checkpoint(
        simulation_id: str,
        round_number: int,
        agent_states: dict[str, AgentState],
        last_active_rounds: list[int],
        total_cost_usd: float = 0.0,
        total_tokens: int = 0,
    ) -> CheckpointData:
        """Create a CheckpointData from current simulation state."""
        return CheckpointData(
            simulation_id=simulation_id,
            round_number=round_number,
            agent_states={aid: state.model_dump() for aid, state in agent_states.items()},
            last_active_rounds=last_active_rounds,
            total_cost_usd=total_cost_usd,
            total_tokens=total_tokens,
        )
