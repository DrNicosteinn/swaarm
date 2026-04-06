"""Tests for LLM adapter layer."""

from app.llm.base import LLMResponse, LLMUsageTracker


class TestLLMResponse:
    def test_basic_response(self):
        response = LLMResponse(
            content="Hello world",
            input_tokens=100,
            output_tokens=20,
            model="gpt-4o-mini",
        )
        assert response.content == "Hello world"
        assert response.input_tokens == 100
        assert len(response.tool_calls) == 0

    def test_tool_call_response(self):
        response = LLMResponse(
            tool_calls=[
                {
                    "id": "call_1",
                    "function": {
                        "name": "create_post",
                        "arguments": '{"content": "Hello"}',
                    },
                }
            ],
            input_tokens=150,
            output_tokens=30,
            model="gpt-4o-mini",
        )
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["function"]["name"] == "create_post"

    def test_cached_tokens(self):
        response = LLMResponse(
            content="Test",
            input_tokens=1000,
            output_tokens=50,
            cached_tokens=800,
            model="gpt-4o-mini",
        )
        assert response.cached_tokens == 800


class TestLLMUsageTracker:
    def test_initial_state(self):
        tracker = LLMUsageTracker(model="gpt-4o-mini")
        assert tracker.total_calls == 0
        assert tracker.total_cost_usd == 0.0

    def test_record_usage(self):
        tracker = LLMUsageTracker(model="gpt-4o-mini")
        response = LLMResponse(
            input_tokens=1000,
            output_tokens=200,
            model="gpt-4o-mini",
        )
        tracker.record(response)

        assert tracker.total_calls == 1
        assert tracker.total_input_tokens == 1000
        assert tracker.total_output_tokens == 200

    def test_cost_calculation(self):
        tracker = LLMUsageTracker(model="gpt-4o-mini")
        # 1M input tokens + 1M output tokens
        response = LLMResponse(
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            model="gpt-4o-mini",
        )
        tracker.record(response)

        # gpt-4o-mini: $0.15/1M input + $0.60/1M output = $0.75
        assert abs(tracker.total_cost_usd - 0.75) < 0.01

    def test_cost_with_caching(self):
        tracker = LLMUsageTracker(model="gpt-4o-mini")
        response = LLMResponse(
            input_tokens=1_000_000,
            output_tokens=1_000_000,
            cached_tokens=800_000,  # 80% cached
            model="gpt-4o-mini",
        )
        tracker.record(response)

        # Uncached: 200k * $0.15/1M = $0.03
        # Cached: 800k * $0.075/1M = $0.06
        # Output: 1M * $0.60/1M = $0.60
        # Total: $0.69
        assert abs(tracker.total_cost_usd - 0.69) < 0.01

    def test_multiple_records(self):
        tracker = LLMUsageTracker(model="gpt-4o-mini")
        for _ in range(5):
            tracker.record(
                LLMResponse(
                    input_tokens=100,
                    output_tokens=50,
                    model="gpt-4o-mini",
                )
            )

        assert tracker.total_calls == 5
        assert tracker.total_input_tokens == 500
        assert tracker.total_output_tokens == 250

    def test_record_error(self):
        tracker = LLMUsageTracker(model="gpt-4o-mini")
        tracker.record_error()
        tracker.record_error()
        assert tracker.total_errors == 2
        assert tracker.total_calls == 0  # errors don't count as calls

    def test_auto_detect_model(self):
        tracker = LLMUsageTracker()
        assert tracker.model == ""

        tracker.record(
            LLMResponse(
                input_tokens=10,
                output_tokens=5,
                model="gpt-4o-mini",
            )
        )
        assert tracker.model == "gpt-4o-mini"
