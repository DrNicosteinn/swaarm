from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.from_object("app.config")

    from app.api.simulation import simulation_bp
    from app.api.report import report_bp

    app.register_blueprint(simulation_bp, url_prefix="/api/simulation")
    app.register_blueprint(report_bp, url_prefix="/api/report")

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    return app
