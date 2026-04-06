"""Simulation quality metrics and analysis.

Computes quality indicators per simulation:
- Shannon entropy (opinion diversity)
- Gini coefficient (engagement distribution)
- Content uniqueness (trigram ratio)
- Quality badge (green/yellow/red)
"""

import math
from collections import Counter

import numpy as np

from app.models.simulation import QualityMetrics, RoundMetrics


def compute_sentiment_entropy(sentiments: list[float]) -> float:
    """Compute Shannon entropy of sentiment distribution.

    Bins sentiments into negative/neutral/positive.
    Target: 0.5-0.8 (healthy diversity). <0.3 = mode collapse.
    """
    if not sentiments:
        return 0.0

    bins = {"negative": 0, "neutral": 0, "positive": 0}
    for s in sentiments:
        if s < -0.2:
            bins["negative"] += 1
        elif s > 0.2:
            bins["positive"] += 1
        else:
            bins["neutral"] += 1

    total = sum(bins.values())
    if total == 0:
        return 0.0

    entropy = 0.0
    for count in bins.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    # Normalize to 0-1 (max entropy for 3 bins = log2(3) ≈ 1.585)
    max_entropy = math.log2(len(bins))
    return entropy / max_entropy if max_entropy > 0 else 0.0


def compute_engagement_gini(engagement_counts: list[int]) -> float:
    """Compute Gini coefficient of engagement distribution.

    Target: 0.5-0.8 (realistic power-law). <0.3 = unrealistically equal.
    >0.9 = one agent dominates everything.
    """
    if not engagement_counts or all(c == 0 for c in engagement_counts):
        return 0.0

    sorted_counts = sorted(engagement_counts)
    n = len(sorted_counts)
    cumulative = np.cumsum(sorted_counts)
    total = cumulative[-1]

    if total == 0:
        return 0.0

    # Gini formula
    gini = (2 * sum((i + 1) * x for i, x in enumerate(sorted_counts))) / (n * total) - (n + 1) / n
    return max(0.0, min(1.0, gini))


def compute_content_uniqueness(texts: list[str]) -> float:
    """Compute unique trigram ratio across all posts.

    Target: >0.6 (good variety). <0.4 = too much repetition.
    """
    if not texts or len(texts) < 2:
        return 1.0

    all_trigrams: list[str] = []
    for text in texts:
        words = text.lower().split()
        for i in range(len(words) - 2):
            trigram = " ".join(words[i : i + 3])
            all_trigrams.append(trigram)

    if not all_trigrams:
        return 1.0

    unique = len(set(all_trigrams))
    total = len(all_trigrams)
    return unique / total


def determine_quality_badge(metrics: QualityMetrics) -> str:
    """Determine quality badge based on all metrics.

    green: All healthy
    yellow: 1-2 warnings
    red: Any critical issue
    """
    warnings = 0
    critical = False

    # Sentiment entropy
    if metrics.sentiment_entropy < 0.3:
        critical = True  # Mode collapse
    elif metrics.sentiment_entropy < 0.5:
        warnings += 1

    # Engagement Gini
    if metrics.engagement_gini > 0.95 or metrics.engagement_gini < 0.2:
        critical = True
    elif metrics.engagement_gini > 0.9 or metrics.engagement_gini < 0.3:
        warnings += 1

    # Content uniqueness
    if metrics.content_uniqueness < 0.4:
        critical = True
    elif metrics.content_uniqueness < 0.6:
        warnings += 1

    if critical:
        return "red"
    if warnings >= 2:
        return "yellow"
    return "green"


def compute_quality_metrics(
    round_metrics_list: list[RoundMetrics],
    all_post_contents: list[str],
    all_sentiments: list[float],
    agent_engagement_counts: list[int],
) -> QualityMetrics:
    """Compute all quality metrics for a completed simulation."""
    entropy = compute_sentiment_entropy(all_sentiments)
    gini = compute_engagement_gini(agent_engagement_counts)
    uniqueness = compute_content_uniqueness(all_post_contents)

    metrics = QualityMetrics(
        sentiment_entropy=round(entropy, 3),
        engagement_gini=round(gini, 3),
        content_uniqueness=round(uniqueness, 3),
        persona_consistency=0.0,  # Requires LLM evaluation — deferred
        clustering_coefficient=0.0,  # Requires graph analysis — deferred
    )

    metrics.quality_badge = determine_quality_badge(metrics)
    return metrics
