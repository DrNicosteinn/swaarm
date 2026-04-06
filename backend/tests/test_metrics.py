"""Tests for simulation quality metrics."""

from app.models.simulation import QualityMetrics
from app.simulation.metrics import (
    compute_content_uniqueness,
    compute_engagement_gini,
    compute_quality_metrics,
    compute_sentiment_entropy,
    determine_quality_badge,
)


class TestSentimentEntropy:
    def test_perfect_diversity(self):
        """Equal distribution → max entropy."""
        sentiments = [-0.5] * 10 + [0.0] * 10 + [0.5] * 10
        entropy = compute_sentiment_entropy(sentiments)
        assert entropy > 0.9  # Near 1.0

    def test_mode_collapse(self):
        """All same sentiment → zero entropy."""
        sentiments = [0.8] * 30
        entropy = compute_sentiment_entropy(sentiments)
        assert entropy < 0.1

    def test_partial_diversity(self):
        """Some diversity but not perfect."""
        sentiments = [-0.5] * 5 + [0.0] * 20 + [0.5] * 5
        entropy = compute_sentiment_entropy(sentiments)
        assert 0.3 < entropy < 0.9

    def test_empty(self):
        assert compute_sentiment_entropy([]) == 0.0


class TestEngagementGini:
    def test_perfect_equality(self):
        """Everyone gets same engagement → Gini near 0."""
        counts = [10] * 20
        gini = compute_engagement_gini(counts)
        assert gini < 0.1

    def test_high_inequality(self):
        """One agent dominates → Gini near 1."""
        counts = [0] * 19 + [100]
        gini = compute_engagement_gini(counts)
        assert gini > 0.8

    def test_realistic_power_law(self):
        """Power-law-like distribution → Gini 0.5-0.8."""
        counts = [1, 1, 2, 2, 3, 5, 5, 8, 15, 50]
        gini = compute_engagement_gini(counts)
        assert 0.3 < gini < 0.9

    def test_empty(self):
        assert compute_engagement_gini([]) == 0.0

    def test_all_zeros(self):
        assert compute_engagement_gini([0, 0, 0]) == 0.0


class TestContentUniqueness:
    def test_unique_content(self):
        """All different posts → high uniqueness."""
        texts = [
            "Die Entlassungen bei SwissBank sind ein Skandal",
            "Employer Branding wird immer wichtiger in der heutigen Zeit",
            "Neue Regulierungen könnten den Markt nachhaltig verändern",
        ]
        uniqueness = compute_content_uniqueness(texts)
        assert uniqueness > 0.8

    def test_repetitive_content(self):
        """Same post repeated → low uniqueness."""
        texts = ["Das ist ein Test post für die Simulation"] * 10
        uniqueness = compute_content_uniqueness(texts)
        assert uniqueness < 0.2

    def test_single_post(self):
        assert compute_content_uniqueness(["Hello"]) == 1.0

    def test_empty(self):
        assert compute_content_uniqueness([]) == 1.0


class TestQualityBadge:
    def test_green_badge(self):
        metrics = QualityMetrics(
            sentiment_entropy=0.7,
            engagement_gini=0.6,
            content_uniqueness=0.8,
        )
        assert determine_quality_badge(metrics) == "green"

    def test_yellow_badge(self):
        metrics = QualityMetrics(
            sentiment_entropy=0.45,  # Warning
            engagement_gini=0.25,  # Warning (below 0.3)
            content_uniqueness=0.8,
        )
        assert determine_quality_badge(metrics) == "yellow"

    def test_red_badge_mode_collapse(self):
        metrics = QualityMetrics(
            sentiment_entropy=0.1,  # Critical
            engagement_gini=0.6,
            content_uniqueness=0.8,
        )
        assert determine_quality_badge(metrics) == "red"

    def test_red_badge_repetition(self):
        metrics = QualityMetrics(
            sentiment_entropy=0.7,
            engagement_gini=0.6,
            content_uniqueness=0.2,  # Critical
        )
        assert determine_quality_badge(metrics) == "red"


class TestComputeQualityMetrics:
    def test_full_computation(self):
        metrics = compute_quality_metrics(
            round_metrics_list=[],
            all_post_contents=[
                "Post eins über die Krise",
                "Post zwei über Employer Branding",
                "Post drei über Regulierung",
            ],
            all_sentiments=[-0.5, 0.0, 0.5, -0.3, 0.2, 0.8],
            agent_engagement_counts=[1, 2, 5, 10, 3, 1],
        )
        assert metrics.quality_badge in ("green", "yellow", "red")
        assert 0 <= metrics.sentiment_entropy <= 1
        assert 0 <= metrics.engagement_gini <= 1
        assert 0 <= metrics.content_uniqueness <= 1
