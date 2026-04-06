"""SQLite database for a single simulation run.

Each simulation gets its own SQLite file for speed and isolation.
After completion, results are persisted to PostgreSQL.
"""

import json
from pathlib import Path

import aiosqlite

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    persona_json TEXT NOT NULL,
    state_json TEXT NOT NULL,
    created_round INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    author_id TEXT NOT NULL,
    content TEXT NOT NULL,
    hashtags TEXT DEFAULT '[]',
    content_format TEXT DEFAULT 'text',
    has_media INTEGER DEFAULT 0,
    has_external_link INTEGER DEFAULT 0,
    created_round INTEGER NOT NULL,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    sentiment REAL DEFAULT 0.0,
    FOREIGN KEY (author_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS comments (
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    content TEXT NOT NULL,
    created_round INTEGER NOT NULL,
    parent_comment_id TEXT,
    sentiment REAL DEFAULT 0.0,
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (author_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS likes (
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    reaction_type TEXT DEFAULT 'like',
    created_round INTEGER NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(post_id, user_id)
);

CREATE TABLE IF NOT EXISTS follows (
    follower_id TEXT NOT NULL,
    followed_id TEXT NOT NULL,
    created_round INTEGER NOT NULL,
    PRIMARY KEY (follower_id, followed_id),
    FOREIGN KEY (follower_id) REFERENCES users(id),
    FOREIGN KEY (followed_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS reposts (
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    created_round INTEGER NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS action_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_number INTEGER NOT NULL,
    agent_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    content TEXT,
    target_id TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS round_metrics (
    round_number INTEGER PRIMARY KEY,
    metrics_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS checkpoints (
    round_number INTEGER PRIMARY KEY,
    state_json TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_posts_round ON posts(created_round);
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_id);
CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_likes_post ON likes(post_id);
CREATE INDEX IF NOT EXISTS idx_action_log_round ON action_log(round_number);
"""


class SimulationDB:
    """Async SQLite database for a single simulation."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self._initialized = False

    async def initialize(self) -> None:
        """Create tables and configure SQLite for performance."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA synchronous=NORMAL")
            await db.execute("PRAGMA cache_size=-65536")  # 64MB
            await db.execute("PRAGMA busy_timeout=5000")
            await db.executescript(SCHEMA_SQL)
            await db.commit()
        self._initialized = True

    async def insert_user(self, user_id: str, name: str, persona_json: str, state_json: str) -> None:
        """Insert a user/agent into the simulation."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO users (id, name, persona_json, state_json) VALUES (?, ?, ?, ?)",
                (user_id, name, persona_json, state_json),
            )
            await db.commit()

    async def insert_users_batch(self, users: list[tuple[str, str, str, str]]) -> None:
        """Batch insert users. Each tuple: (id, name, persona_json, state_json)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executemany(
                "INSERT OR REPLACE INTO users (id, name, persona_json, state_json) VALUES (?, ?, ?, ?)",
                users,
            )
            await db.commit()

    async def insert_post(
        self,
        post_id: str,
        author_id: str,
        content: str,
        created_round: int,
        hashtags: list[str] | None = None,
        content_format: str = "text",
        has_media: bool = False,
        has_external_link: bool = False,
    ) -> None:
        """Insert a new post."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO posts (id, author_id, content, hashtags, content_format,
                   has_media, has_external_link, created_round)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    post_id,
                    author_id,
                    content,
                    json.dumps(hashtags or []),
                    content_format,
                    int(has_media),
                    int(has_external_link),
                    created_round,
                ),
            )
            await db.commit()

    async def insert_comment(
        self,
        comment_id: str,
        post_id: str,
        author_id: str,
        content: str,
        created_round: int,
        parent_comment_id: str | None = None,
    ) -> None:
        """Insert a comment on a post."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO comments (id, post_id, author_id, content, created_round, parent_comment_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (comment_id, post_id, author_id, content, created_round, parent_comment_id),
            )
            # Increment comment count on post
            await db.execute("UPDATE posts SET comments = comments + 1 WHERE id = ?", (post_id,))
            await db.commit()

    async def insert_like(
        self,
        like_id: str,
        post_id: str,
        user_id: str,
        created_round: int,
        reaction_type: str = "like",
    ) -> None:
        """Insert a like/reaction. Ignores duplicates."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT OR IGNORE INTO likes (id, post_id, user_id, reaction_type, created_round)
                   VALUES (?, ?, ?, ?, ?)""",
                (like_id, post_id, user_id, reaction_type, created_round),
            )
            await db.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
            await db.commit()

    async def insert_follow(self, follower_id: str, followed_id: str, created_round: int) -> None:
        """Insert a follow relationship. Ignores duplicates."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO follows (follower_id, followed_id, created_round) VALUES (?, ?, ?)",
                (follower_id, followed_id, created_round),
            )
            await db.commit()

    async def insert_repost(self, repost_id: str, post_id: str, user_id: str, created_round: int) -> None:
        """Insert a repost/share."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO reposts (id, post_id, user_id, created_round) VALUES (?, ?, ?, ?)",
                (repost_id, post_id, user_id, created_round),
            )
            await db.execute("UPDATE posts SET reposts = reposts + 1 WHERE id = ?", (post_id,))
            await db.commit()

    async def log_action(
        self,
        round_number: int,
        agent_id: str,
        action_type: str,
        content: str | None = None,
        target_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Log an agent action for audit trail."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO action_log (round_number, agent_id, action_type, content, target_id, metadata)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    round_number,
                    agent_id,
                    action_type,
                    content,
                    target_id,
                    json.dumps(metadata or {}),
                ),
            )
            await db.commit()

    async def log_actions_batch(self, actions: list[tuple]) -> None:
        """Batch log actions.

        Each tuple: (round, agent_id, action_type, content, target_id, metadata_json).
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.executemany(
                """INSERT INTO action_log (round_number, agent_id, action_type, content, target_id, metadata)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                actions,
            )
            await db.commit()

    async def get_posts_for_feed(self, max_round: int, limit: int = 100) -> list[dict]:
        """Get recent posts for feed generation."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT id, author_id, content, hashtags, content_format,
                          has_media, has_external_link, created_round,
                          likes, comments, reposts, sentiment
                   FROM posts
                   WHERE created_round <= ?
                   ORDER BY created_round DESC, likes DESC
                   LIMIT ?""",
                (max_round, limit),
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_user_following(self, user_id: str) -> list[str]:
        """Get list of user IDs that this user follows."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT followed_id FROM follows WHERE follower_id = ?",
                (user_id,),
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def get_round_action_count(self, round_number: int) -> dict[str, int]:
        """Get action counts for a specific round."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT action_type, COUNT(*) as count
                   FROM action_log
                   WHERE round_number = ?
                   GROUP BY action_type""",
                (round_number,),
            )
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}

    async def save_round_metrics(self, round_number: int, metrics_json: str) -> None:
        """Save metrics for a completed round."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO round_metrics (round_number, metrics_json) VALUES (?, ?)",
                (round_number, metrics_json),
            )
            await db.commit()

    async def get_total_post_count(self) -> int:
        """Get total number of posts in the simulation."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM posts")
            row = await cursor.fetchone()
            return row[0] if row else 0
