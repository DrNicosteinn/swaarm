import uuid
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

from app.config import OASIS_SIMULATION_DATA_DIR


class SimulationStatus(str, Enum):
    CREATED = "created"
    GENERATING_PERSONAS = "generating_personas"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class SimulationRequest:
    scenario: str
    context: str = ""
    target_audience: str = ""
    num_agents: int = 50
    num_rounds: int = 20
    platform: str = "twitter"


@dataclass
class Simulation:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    scenario: str = ""
    context: str = ""
    target_audience: str = ""
    num_agents: int = 50
    num_rounds: int = 20
    platform: str = "twitter"
    status: SimulationStatus = SimulationStatus.CREATED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    current_round: int = 0
    total_actions: int = 0
    error: str | None = None

    @property
    def data_dir(self) -> str:
        path = os.path.join(OASIS_SIMULATION_DATA_DIR, self.id)
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def profiles_path(self) -> str:
        return os.path.join(self.data_dir, "profiles.csv")

    @property
    def actions_path(self) -> str:
        return os.path.join(self.data_dir, "actions.jsonl")

    @property
    def report_path(self) -> str:
        return os.path.join(self.data_dir, "report.md")

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self):
        path = os.path.join(self.data_dir, "simulation.json")
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, sim_id: str) -> "Simulation":
        path = os.path.join(OASIS_SIMULATION_DATA_DIR, sim_id, "simulation.json")
        with open(path) as f:
            data = json.load(f)
        data["status"] = SimulationStatus(data["status"])
        return cls(**data)


# In-memory store for active simulations
_simulations: dict[str, Simulation] = {}


def get_simulation(sim_id: str) -> Simulation | None:
    if sim_id in _simulations:
        return _simulations[sim_id]
    try:
        sim = Simulation.load(sim_id)
        _simulations[sim_id] = sim
        return sim
    except FileNotFoundError:
        return None


def create_simulation(req: SimulationRequest) -> Simulation:
    sim = Simulation(
        scenario=req.scenario,
        context=req.context,
        target_audience=req.target_audience,
        num_agents=req.num_agents,
        num_rounds=req.num_rounds,
        platform=req.platform,
    )
    sim.save()
    _simulations[sim.id] = sim
    return sim
