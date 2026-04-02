import json
import os
import threading

from flask import Blueprint, request, jsonify

from app.models.simulation import (
    SimulationRequest,
    SimulationStatus,
    create_simulation,
    get_simulation,
)
from app.services.persona_generator import generate_personas
from app.services.simulation_runner import run_simulation
from app.utils.logger import get_logger

logger = get_logger(__name__)
simulation_bp = Blueprint("simulation", __name__)


@simulation_bp.route("/create", methods=["POST"])
def create():
    data = request.json
    req = SimulationRequest(
        scenario=data["scenario"],
        context=data.get("context", ""),
        target_audience=data.get("target_audience", ""),
        num_agents=data.get("num_agents", 50),
        num_rounds=data.get("num_rounds", 20),
        platform=data.get("platform", "twitter"),
    )
    sim = create_simulation(req)

    # Generate personas in background
    def _generate():
        try:
            sim.status = SimulationStatus.GENERATING_PERSONAS
            sim.save()
            generate_personas(sim)
            sim.status = SimulationStatus.READY
            sim.save()
            logger.info(f"Simulation {sim.id}: personas ready")
        except Exception as e:
            sim.status = SimulationStatus.FAILED
            sim.error = str(e)
            sim.save()
            logger.error(f"Simulation {sim.id}: persona generation failed: {e}")

    threading.Thread(target=_generate, daemon=True).start()
    return jsonify(sim.to_dict()), 201


@simulation_bp.route("/run/<sim_id>", methods=["POST"])
def run(sim_id):
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404
    if sim.status != SimulationStatus.READY:
        return jsonify({"error": f"Cannot run: status is {sim.status}"}), 400

    # Run simulation in background
    def _run():
        try:
            sim.status = SimulationStatus.RUNNING
            sim.save()
            run_simulation(sim)
            sim.status = SimulationStatus.COMPLETED
            sim.save()
            logger.info(f"Simulation {sim.id}: completed")
        except Exception as e:
            sim.status = SimulationStatus.FAILED
            sim.error = str(e)
            sim.save()
            logger.error(f"Simulation {sim.id}: run failed: {e}")

    threading.Thread(target=_run, daemon=True).start()
    return jsonify(sim.to_dict())


@simulation_bp.route("/status/<sim_id>")
def status(sim_id):
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404
    return jsonify(sim.to_dict())


@simulation_bp.route("/actions/<sim_id>")
def actions(sim_id):
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404

    offset = request.args.get("offset", 0, type=int)
    limit = request.args.get("limit", 50, type=int)

    actions_list = []
    if os.path.exists(sim.actions_path):
        with open(sim.actions_path) as f:
            lines = f.readlines()
        for line in lines[offset : offset + limit]:
            try:
                actions_list.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue

    return jsonify(
        {
            "actions": actions_list,
            "total": sim.total_actions,
            "offset": offset,
            "limit": limit,
        }
    )


@simulation_bp.route("/stop/<sim_id>", methods=["POST"])
def stop(sim_id):
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404
    sim.status = SimulationStatus.STOPPED
    sim.save()
    return jsonify(sim.to_dict())
