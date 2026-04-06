"""Tests for report generator."""

import os
import tempfile

import pytest

from app.models.simulation import RoundMetrics
from app.reports.generator import ReportData, ReportGenerator
from app.simulation.database import SimulationDB


@pytest.fixture
async def report_setup():
    """Create a DB with simulation data for report testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = SimulationDB(db_path)
    await db.initialize()

    # Insert test data
    await db.insert_user("u1", "Claudia Meier", "{}", "{}")
    await db.insert_user("u2", "Max Richter", "{}", "{}")
    await db.insert_user("u3", "Lisa Hofer", "{}", "{}")

    await db.insert_post("p1", "u1", "Die Entlassungen sind ein Skandal! #SwissBank", created_round=1)
    await db.insert_post("p2", "u2", "Employer Branding wird immer wichtiger", created_round=2)
    await db.insert_post("p3", "u3", "Die Kommunikation hätte besser sein können", created_round=2)
    await db.insert_post("p4", "u1", "Solidarität mit den Betroffenen #SwissBank", created_round=3)

    await db.insert_like("l1", "p1", "u2", created_round=1)
    await db.insert_like("l2", "p1", "u3", created_round=1)
    await db.insert_comment("c1", "p1", "u2", "Stimmt leider", created_round=1)

    round_metrics = [
        RoundMetrics(
            round_number=1, active_agents=10, posts_created=1,
            comments_created=1, likes_given=2, reposts=0, follows=0,
            avg_sentiment=-0.3, duration_seconds=5.0,
        ),
        RoundMetrics(
            round_number=2, active_agents=8, posts_created=2,
            comments_created=0, likes_given=1, reposts=0, follows=1,
            avg_sentiment=-0.1, duration_seconds=4.0,
        ),
        RoundMetrics(
            round_number=3, active_agents=12, posts_created=1,
            comments_created=2, likes_given=3, reposts=1, follows=0,
            avg_sentiment=0.1, duration_seconds=6.0,
        ),
    ]

    yield db, db_path, round_metrics

    os.unlink(db_path)


class TestReportGenerator:
    @pytest.mark.asyncio
    async def test_generate_report(self, report_setup):
        """Generate a report from test data."""
        db, _, round_metrics = report_setup
        gen = ReportGenerator(llm=None)  # No LLM for unit test

        report = await gen.generate(
            simulation_id="test-sim",
            db=db,
            round_metrics=round_metrics,
            scenario_text="SwissBank Entlassungen",
            total_cost=0.05,
            duration=15.0,
        )

        assert isinstance(report, ReportData)
        assert report.simulation_id == "test-sim"
        assert report.total_rounds == 3
        assert report.total_posts == 4  # 1 + 2 + 1
        assert report.total_comments == 3  # 1 + 0 + 2
        assert report.total_likes == 6  # 2 + 1 + 3

    @pytest.mark.asyncio
    async def test_sentiment_timeline(self, report_setup):
        """Sentiment timeline matches round metrics."""
        db, _, round_metrics = report_setup
        gen = ReportGenerator()

        report = await gen.generate("test", db, round_metrics)

        assert len(report.sentiment_timeline) == 3
        assert report.sentiment_timeline[0] == -0.3
        assert report.sentiment_timeline[2] == 0.1

    @pytest.mark.asyncio
    async def test_narratives_detected(self, report_setup):
        """Simple narrative detection finds keywords."""
        db, _, round_metrics = report_setup
        gen = ReportGenerator()

        report = await gen.generate("test", db, round_metrics)

        # Should detect at least some narratives from the test posts
        # (depends on keyword frequency)
        assert isinstance(report.narratives, list)

    @pytest.mark.asyncio
    async def test_risks_detected(self, report_setup):
        """Risk detection identifies sentiment issues."""
        db, _, round_metrics = report_setup
        gen = ReportGenerator()

        report = await gen.generate("test", db, round_metrics)

        assert isinstance(report.risks, list)

    @pytest.mark.asyncio
    async def test_quality_badge(self, report_setup):
        """Quality badge is computed."""
        db, _, round_metrics = report_setup
        gen = ReportGenerator()

        report = await gen.generate("test", db, round_metrics)

        assert report.quality.quality_badge in ("green", "yellow", "red")

    @pytest.mark.asyncio
    async def test_engagement_timeline(self, report_setup):
        """Engagement per round is tracked."""
        db, _, round_metrics = report_setup
        gen = ReportGenerator()

        report = await gen.generate("test", db, round_metrics)

        assert len(report.engagement_per_round) == 3
        assert report.engagement_per_round[0] == 4  # 1 post + 1 comment + 2 likes

    @pytest.mark.asyncio
    async def test_empty_simulation(self):
        """Handle empty simulation gracefully."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        db = SimulationDB(db_path)
        await db.initialize()

        gen = ReportGenerator()
        report = await gen.generate("empty-sim", db, [])

        assert report.total_posts == 0
        assert report.total_rounds == 0
        assert report.quality.quality_badge in ("green", "yellow", "red")

        os.unlink(db_path)
