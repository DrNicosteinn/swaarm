"""Tests for simulation resilience and circuit breaker."""

from app.simulation.resilience import HealthMonitor, SimulationAction


class TestHealthMonitor:
    def test_initial_state(self):
        monitor = HealthMonitor(total_agents=100)
        status = monitor.get_status()
        assert status["total_errors"] == 0
        assert status["failure_rate"] == 0.0

    def test_success_resets_consecutive(self):
        monitor = HealthMonitor(total_agents=100)
        monitor.consecutive_errors = 10
        monitor.record_success()
        assert monitor.consecutive_errors == 0

    def test_single_failure_continues(self):
        monitor = HealthMonitor(total_agents=100)
        action = monitor.record_failure("agent-1", "timeout")
        assert action == SimulationAction.CONTINUE
        assert monitor.total_errors == 1

    def test_circuit_breaker_pauses(self):
        """More than 15% failures triggers pause."""
        monitor = HealthMonitor(total_agents=100, failure_threshold=0.15)
        # Fail 16 different agents
        for i in range(16):
            action = monitor.record_failure(f"agent-{i}", "error")
        assert action == SimulationAction.PAUSE

    def test_consecutive_errors_slow_down(self):
        """50+ consecutive errors triggers slow down."""
        monitor = HealthMonitor(total_agents=1000, consecutive_error_limit=50)
        for i in range(51):
            action = monitor.record_failure(f"agent-{i}", "error")
        assert action == SimulationAction.SLOW_DOWN

    def test_budget_exceeded_stops(self):
        monitor = HealthMonitor(total_agents=100, budget_limit_usd=1.0)
        action = monitor.record_cost(0.5)
        assert action == SimulationAction.CONTINUE

        action = monitor.record_cost(0.6)
        assert action == SimulationAction.STOP

    def test_no_budget_limit(self):
        monitor = HealthMonitor(total_agents=100)
        action = monitor.record_cost(1000.0)
        assert action == SimulationAction.CONTINUE

    def test_round_reset(self):
        monitor = HealthMonitor(total_agents=100)
        monitor.round_failures = 5
        monitor.reset_round()
        assert monitor.round_failures == 0
        # Total errors should NOT reset
        assert monitor.total_errors == 0

    def test_duplicate_agent_counted_once(self):
        """Same agent failing twice still counts as 1 failed agent."""
        monitor = HealthMonitor(total_agents=100)
        monitor.record_failure("agent-1", "error1")
        monitor.record_failure("agent-1", "error2")
        assert len(monitor.failed_agents) == 1
        assert monitor.total_errors == 2

    def test_status_report(self):
        monitor = HealthMonitor(total_agents=100, budget_limit_usd=5.0)
        monitor.record_failure("agent-1", "error")
        monitor.record_cost(1.5)

        status = monitor.get_status()
        assert status["total_errors"] == 1
        assert status["failed_agents"] == 1
        assert status["failure_rate"] == 0.01
        assert status["current_cost_usd"] == 1.5
        assert status["budget_remaining_usd"] == 3.5
