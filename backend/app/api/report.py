import os

from flask import Blueprint, request, jsonify

from app.models.simulation import SimulationStatus, get_simulation
from app.services.report_agent import generate_report, chat_with_report
from app.utils.logger import get_logger

logger = get_logger(__name__)
report_bp = Blueprint("report", __name__)


@report_bp.route("/generate/<sim_id>", methods=["POST"])
def generate(sim_id):
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404
    if sim.status != SimulationStatus.COMPLETED:
        return jsonify({"error": f"Simulation not completed: {sim.status}"}), 400

    try:
        report = generate_report(sim)
        return jsonify({"report": report, "simulation_id": sim_id})
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return jsonify({"error": str(e)}), 500


@report_bp.route("/get/<sim_id>")
def get_report(sim_id):
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404

    if not os.path.exists(sim.report_path):
        return jsonify({"error": "Report not generated yet"}), 404

    with open(sim.report_path) as f:
        report = f.read()
    return jsonify({"report": report, "simulation_id": sim_id})


@report_bp.route("/chat/<sim_id>", methods=["POST"])
def chat(sim_id):
    sim = get_simulation(sim_id)
    if not sim:
        return jsonify({"error": "Simulation not found"}), 404

    data = request.json
    message = data.get("message", "")
    history = data.get("history", [])

    try:
        response = chat_with_report(sim, message, history)
        return jsonify({"response": response})
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        return jsonify({"error": str(e)}), 500
