"""Report generator — creates analysis reports from simulation results.

Produces:
1. Structured report data (for interactive dashboard)
2. LLM-generated summary text (executive summary in German)
3. PDF export
"""

from datetime import UTC, datetime

from loguru import logger
from pydantic import BaseModel, Field

from app.llm.base import LLMProvider
from app.models.simulation import QualityMetrics, RoundMetrics
from app.simulation.database import SimulationDB
from app.simulation.metrics import compute_quality_metrics


class NarrativeItem(BaseModel):
    """A detected narrative/topic in the simulation."""

    label: str
    post_count: int
    sentiment: float
    representative_posts: list[str] = Field(default_factory=list)


class RiskItem(BaseModel):
    """An identified risk from the simulation."""

    level: str  # "hoch", "mittel", "niedrig"
    description: str
    round_detected: int = 0


class ReportData(BaseModel):
    """Complete report data for the dashboard."""

    simulation_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    # Summary
    executive_summary: str = ""
    total_rounds: int = 0
    total_agents: int = 0
    total_posts: int = 0
    total_comments: int = 0
    total_likes: int = 0

    # Sentiment over time
    sentiment_timeline: list[float] = Field(default_factory=list)

    # Engagement over time
    posts_per_round: list[int] = Field(default_factory=list)
    engagement_per_round: list[int] = Field(default_factory=list)

    # Narratives
    narratives: list[NarrativeItem] = Field(default_factory=list)

    # Risks
    risks: list[RiskItem] = Field(default_factory=list)

    # Quality
    quality: QualityMetrics = Field(default_factory=QualityMetrics)

    # Cost
    total_cost_usd: float = 0.0
    duration_seconds: float = 0.0


SUMMARY_PROMPT = (
    "Du bist ein Kommunikationsexperte. Analysiere diese Simulationsergebnisse "
    "und schreibe eine Executive Summary auf Deutsch (max 200 Wörter).\n\n"
    "Szenario: {scenario}\n"
    "Runden: {rounds}\n"
    "Agents: {agents}\n"
    "Posts: {posts}, Kommentare: {comments}, Likes: {likes}\n"
    "Sentiment-Verlauf: {sentiment_trend}\n"
    "Häufigste Themen: {topics}\n\n"
    "Schreibe eine professionelle Zusammenfassung mit:\n"
    "1. Haupterkenntnis (1 Satz)\n"
    "2. Sentiment-Entwicklung\n"
    "3. Identifizierte Risiken\n"
    "4. Empfehlung (1-2 Sätze)\n\n"
    "WICHTIG: Formuliere als vergleichende Szenario-Analyse, "
    "NICHT als statistische Vorhersage."
)


class ReportGenerator:
    """Generates analysis reports from simulation data."""

    def __init__(self, llm: LLMProvider | None = None):
        self.llm = llm

    async def generate(
        self,
        simulation_id: str,
        db: SimulationDB,
        round_metrics: list[RoundMetrics],
        scenario_text: str = "",
        total_cost: float = 0.0,
        duration: float = 0.0,
    ) -> ReportData:
        """Generate a complete report from simulation data."""
        logger.info(f"Generating report for simulation {simulation_id}")

        # Collect data from DB
        all_posts = await db.get_posts_for_feed(max_round=9999, limit=10000)
        await db.get_total_post_count()

        # Build timeline data
        sentiment_timeline = [m.avg_sentiment for m in round_metrics]
        posts_per_round = [m.posts_created for m in round_metrics]
        engagement_per_round = [
            m.posts_created + m.comments_created + m.likes_given for m in round_metrics
        ]

        # Compute totals
        total_posts = sum(m.posts_created for m in round_metrics)
        total_comments = sum(m.comments_created for m in round_metrics)
        total_likes = sum(m.likes_given for m in round_metrics)

        # Extract post contents and sentiments for quality metrics
        post_contents = [p["content"] for p in all_posts if p.get("content")]
        post_sentiments = [p.get("sentiment", 0.0) for p in all_posts]
        agent_engagements = self._compute_agent_engagement(all_posts)

        # Compute quality metrics
        quality = compute_quality_metrics(
            round_metrics_list=round_metrics,
            all_post_contents=post_contents,
            all_sentiments=post_sentiments,
            agent_engagement_counts=agent_engagements,
        )

        # Detect narratives (simplified: group by most common words)
        narratives = self._detect_simple_narratives(all_posts)

        # Detect risks
        risks = self._detect_risks(sentiment_timeline, round_metrics)

        # Generate executive summary via LLM
        summary = ""
        if self.llm and post_contents:
            summary = await self._generate_summary(
                scenario_text, round_metrics, narratives, total_posts, total_comments, total_likes
            )

        report = ReportData(
            simulation_id=simulation_id,
            executive_summary=summary,
            total_rounds=len(round_metrics),
            total_agents=round_metrics[0].active_agents if round_metrics else 0,
            total_posts=total_posts,
            total_comments=total_comments,
            total_likes=total_likes,
            sentiment_timeline=sentiment_timeline,
            posts_per_round=posts_per_round,
            engagement_per_round=engagement_per_round,
            narratives=narratives,
            risks=risks,
            quality=quality,
            total_cost_usd=total_cost,
            duration_seconds=duration,
        )

        logger.info(
            f"Report generated: {total_posts} posts, {len(narratives)} narratives, "
            f"{len(risks)} risks, badge={quality.quality_badge}"
        )

        return report

    def _compute_agent_engagement(self, posts: list[dict]) -> list[int]:
        """Compute total engagement per agent."""
        agent_engagement: dict[str, int] = {}
        for post in posts:
            author = post.get("author_id", "")
            engagement = post.get("likes", 0) + post.get("comments", 0) + post.get("reposts", 0)
            agent_engagement[author] = agent_engagement.get(author, 0) + engagement
        return list(agent_engagement.values()) if agent_engagement else [0]

    def _detect_simple_narratives(self, posts: list[dict]) -> list[NarrativeItem]:
        """Simple narrative detection via keyword frequency.

        This is a placeholder — the full version uses embedding-based
        clustering (see SIMULATION_ENGINE_BLUEPRINT.md Teil 18).
        """
        if not posts:
            return []

        # Count word frequencies across all posts
        word_counts: dict[str, int] = {}
        post_by_word: dict[str, list[str]] = {}

        stopwords = {
            "die", "der", "das", "und", "ist", "in", "von", "zu", "für", "mit",
            "auf", "ein", "eine", "es", "nicht", "sich", "den", "auch", "ich",
            "an", "des", "als", "hat", "wie", "bei", "man", "noch", "so",
            "dass", "aber", "nach", "wird", "wir", "sie", "er", "was", "kann",
            "aus", "über", "nur", "sind", "haben", "wurde", "dem", "schon",
        }

        for post in posts:
            content = post.get("content", "")
            words = content.lower().split()
            seen_words: set[str] = set()
            for word in words:
                word = word.strip(".,!?;:()\"'")
                if len(word) < 4 or word in stopwords:
                    continue
                if word not in seen_words:
                    word_counts[word] = word_counts.get(word, 0) + 1
                    post_by_word.setdefault(word, []).append(content[:100])
                    seen_words.add(word)

        # Top keywords as narratives
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        narratives = []
        for word, count in sorted_words[:5]:
            if count < 2:
                break
            narratives.append(NarrativeItem(
                label=word.capitalize(),
                post_count=count,
                sentiment=0.0,  # Would need sentiment analysis
                representative_posts=post_by_word.get(word, [])[:3],
            ))

        return narratives

    def _detect_risks(
        self, sentiment_timeline: list[float], round_metrics: list[RoundMetrics]
    ) -> list[RiskItem]:
        """Detect risks based on sentiment drops and engagement spikes."""
        risks = []

        # Risk: Sentiment drops significantly
        for i in range(1, len(sentiment_timeline)):
            drop = sentiment_timeline[i - 1] - sentiment_timeline[i]
            if drop > 0.3:
                risks.append(RiskItem(
                    level="hoch",
                    description=(
                        f"Stimmungseinbruch in Runde {i + 1}: "
                        f"Sentiment fiel um {drop:.2f} Punkte"
                    ),
                    round_detected=i + 1,
                ))

        # Risk: Very negative overall sentiment
        if sentiment_timeline:
            avg = sum(sentiment_timeline) / len(sentiment_timeline)
            if avg < -0.3:
                risks.append(RiskItem(
                    level="hoch",
                    description=f"Durchgehend negatives Sentiment (Durchschnitt: {avg:.2f})",
                ))

        # Risk: High error rate
        for m in round_metrics:
            if m.error_count > 0 and m.active_agents > 0:
                error_rate = m.error_count / m.active_agents
                if error_rate > 0.1:
                    risks.append(RiskItem(
                        level="mittel",
                        description=f"Hohe Fehlerrate in Runde {m.round_number} ({error_rate:.0%})",
                        round_detected=m.round_number,
                    ))

        return risks[:10]  # Max 10 risks

    async def _generate_summary(
        self,
        scenario: str,
        round_metrics: list[RoundMetrics],
        narratives: list[NarrativeItem],
        total_posts: int,
        total_comments: int,
        total_likes: int,
    ) -> str:
        """Generate executive summary via LLM."""
        if not self.llm:
            return ""

        sentiment_values = [m.avg_sentiment for m in round_metrics]
        trend = "steigend" if sentiment_values[-1] > sentiment_values[0] else "fallend"
        topics = ", ".join(n.label for n in narratives[:5]) or "keine erkannt"

        prompt = SUMMARY_PROMPT.format(
            scenario=scenario[:300],
            rounds=len(round_metrics),
            agents=round_metrics[0].active_agents if round_metrics else 0,
            posts=total_posts,
            comments=total_comments,
            likes=total_likes,
            sentiment_trend=f"{trend} ({sentiment_values[0]:.2f} → {sentiment_values[-1]:.2f})",
            topics=topics,
        )

        try:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            return (response.content or "").strip()[:1000]
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            return "Executive Summary konnte nicht generiert werden."
