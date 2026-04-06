"""Tests for simulation SQLite database."""

import json
import os
import tempfile

import pytest

from app.simulation.database import SimulationDB


@pytest.fixture
async def db():
    """Create a temporary simulation database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    sim_db = SimulationDB(db_path)
    await sim_db.initialize()
    yield sim_db

    os.unlink(db_path)


@pytest.mark.asyncio
async def test_initialize_creates_tables(db: SimulationDB):
    """Database initialization creates all required tables."""
    import aiosqlite

    async with aiosqlite.connect(db.db_path) as conn:
        cursor = await conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in await cursor.fetchall()]

    assert "users" in tables
    assert "posts" in tables
    assert "comments" in tables
    assert "likes" in tables
    assert "follows" in tables
    assert "reposts" in tables
    assert "action_log" in tables
    assert "round_metrics" in tables
    assert "checkpoints" in tables


@pytest.mark.asyncio
async def test_insert_and_read_user(db: SimulationDB):
    """Can insert and retrieve a user."""
    await db.insert_user("u1", "Claudia Meier", '{"id": "u1"}', '{"sentiment": 0.0}')

    import aiosqlite

    async with aiosqlite.connect(db.db_path) as conn:
        cursor = await conn.execute("SELECT * FROM users WHERE id = 'u1'")
        row = await cursor.fetchone()

    assert row is not None
    assert row[1] == "Claudia Meier"


@pytest.mark.asyncio
async def test_batch_insert_users(db: SimulationDB):
    """Batch insert multiple users."""
    users = [
        ("u1", "Alice", "{}", "{}"),
        ("u2", "Bob", "{}", "{}"),
        ("u3", "Charlie", "{}", "{}"),
    ]
    await db.insert_users_batch(users)

    import aiosqlite

    async with aiosqlite.connect(db.db_path) as conn:
        cursor = await conn.execute("SELECT COUNT(*) FROM users")
        count = (await cursor.fetchone())[0]

    assert count == 3


@pytest.mark.asyncio
async def test_insert_post_and_like(db: SimulationDB):
    """Insert a post, then like it — like count increments."""
    await db.insert_user("u1", "Test User", "{}", "{}")
    await db.insert_post("p1", "u1", "Hello World", created_round=1, hashtags=["test"])

    await db.insert_user("u2", "Liker", "{}", "{}")
    await db.insert_like("l1", "p1", "u2", created_round=1)

    import aiosqlite

    async with aiosqlite.connect(db.db_path) as conn:
        cursor = await conn.execute("SELECT likes FROM posts WHERE id = 'p1'")
        likes = (await cursor.fetchone())[0]

    assert likes == 1


@pytest.mark.asyncio
async def test_insert_comment_increments_count(db: SimulationDB):
    """Commenting on a post increments its comment count."""
    await db.insert_user("u1", "Author", "{}", "{}")
    await db.insert_post("p1", "u1", "Original post", created_round=1)

    await db.insert_user("u2", "Commenter", "{}", "{}")
    await db.insert_comment("c1", "p1", "u2", "Great post!", created_round=1)

    import aiosqlite

    async with aiosqlite.connect(db.db_path) as conn:
        cursor = await conn.execute("SELECT comments FROM posts WHERE id = 'p1'")
        comments = (await cursor.fetchone())[0]

    assert comments == 1


@pytest.mark.asyncio
async def test_follow_and_get_following(db: SimulationDB):
    """Follow a user and retrieve following list."""
    await db.insert_user("u1", "Follower", "{}", "{}")
    await db.insert_user("u2", "Followed", "{}", "{}")
    await db.insert_follow("u1", "u2", created_round=1)

    following = await db.get_user_following("u1")
    assert "u2" in following


@pytest.mark.asyncio
async def test_duplicate_like_ignored(db: SimulationDB):
    """Duplicate likes are silently ignored."""
    await db.insert_user("u1", "Author", "{}", "{}")
    await db.insert_post("p1", "u1", "Post", created_round=1)
    await db.insert_user("u2", "Liker", "{}", "{}")

    await db.insert_like("l1", "p1", "u2", created_round=1)
    await db.insert_like("l1", "p1", "u2", created_round=1)  # duplicate — should not error


@pytest.mark.asyncio
async def test_get_posts_for_feed(db: SimulationDB):
    """Feed query returns posts ordered by round and engagement."""
    await db.insert_user("u1", "Author", "{}", "{}")
    await db.insert_post("p1", "u1", "Old post", created_round=1)
    await db.insert_post("p2", "u1", "New post", created_round=3)
    await db.insert_post("p3", "u1", "Future post", created_round=10)

    # Feed at round 5 should not include round 10
    feed = await db.get_posts_for_feed(max_round=5)
    post_ids = [p["id"] for p in feed]
    assert "p1" in post_ids
    assert "p2" in post_ids
    assert "p3" not in post_ids


@pytest.mark.asyncio
async def test_action_log_and_count(db: SimulationDB):
    """Log actions and retrieve counts per round."""
    await db.log_action(1, "u1", "create_post", content="Hello")
    await db.log_action(1, "u2", "like_post", target_id="p1")
    await db.log_action(1, "u3", "like_post", target_id="p1")

    counts = await db.get_round_action_count(1)
    assert counts["create_post"] == 1
    assert counts["like_post"] == 2


@pytest.mark.asyncio
async def test_batch_action_log(db: SimulationDB):
    """Batch logging actions."""
    actions = [
        (1, "u1", "create_post", "Hello", None, "{}"),
        (1, "u2", "like_post", None, "p1", "{}"),
        (1, "u3", "comment", "Nice!", "p1", "{}"),
    ]
    await db.log_actions_batch(actions)

    counts = await db.get_round_action_count(1)
    assert sum(counts.values()) == 3


@pytest.mark.asyncio
async def test_total_post_count(db: SimulationDB):
    """Get total post count."""
    await db.insert_user("u1", "Author", "{}", "{}")
    assert await db.get_total_post_count() == 0

    await db.insert_post("p1", "u1", "Post 1", created_round=1)
    await db.insert_post("p2", "u1", "Post 2", created_round=2)
    assert await db.get_total_post_count() == 2
