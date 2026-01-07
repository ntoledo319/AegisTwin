"""
PostgreSQL Storage Backend

Provides PostgreSQL-backed storage for traces and audits.

@ai_prompt: Use PostgresTraceStore for production deployments
@context_boundary: aegistwin/storage/postgres
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from aegistwin.storage.base import AuditStore, TraceStore

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False


@dataclass
class PostgresConfig:
    """PostgreSQL connection configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "aegistwin"
    user: str = "aegistwin"
    password: str = "aegistwin"
    min_connections: int = 2
    max_connections: int = 10


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    run_id VARCHAR(32) PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    source VARCHAR(255),
    event_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    run_id VARCHAR(32) REFERENCES runs(run_id) ON DELETE CASCADE,
    event_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    payload_hash VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    actor VARCHAR(255) NOT NULL,
    action VARCHAR(255) NOT NULL,
    resource VARCHAR(255) NOT NULL,
    outcome VARCHAR(64) NOT NULL,
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
"""


class PostgresTraceStore(TraceStore):
    """
    PostgreSQL-backed trace storage.

    Attributes:
        config: PostgreSQL connection config
        pool: Connection pool
    """

    def __init__(self, config: PostgresConfig | None = None):
        if not HAS_ASYNCPG:
            raise RuntimeError("asyncpg not installed. Install with: pip install asyncpg")

        self.config = config or PostgresConfig()
        self._pool: asyncpg.Pool | None = None

    async def connect(self) -> None:
        """Establish connection pool."""
        self._pool = await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            database=self.config.database,
            user=self.config.user,
            password=self.config.password,
            min_size=self.config.min_connections,
            max_size=self.config.max_connections,
        )

        async with self._pool.acquire() as conn:
            await conn.execute(SCHEMA_SQL)

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def save_trace(self, run_id: str, events: list[dict]) -> None:
        """Save event trace for a run."""
        if not self._pool:
            raise RuntimeError("Not connected")

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO runs (run_id, event_count, completed_at)
                    VALUES ($1, $2, NOW())
                    ON CONFLICT (run_id) DO UPDATE
                    SET event_count = $2, completed_at = NOW()
                    """,
                    run_id,
                    len(events),
                )

                for event in events:
                    await conn.execute(
                        """
                        INSERT INTO events (run_id, event_id, event_type, timestamp, payload, payload_hash)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                        run_id,
                        event.get("event_id"),
                        event.get("event_type"),
                        datetime.fromisoformat(event.get("timestamp", datetime.now(timezone.utc).isoformat())),
                        json.dumps(event),
                        event.get("payload_hash"),
                    )

    async def load_trace(self, run_id: str) -> list[dict] | None:
        """Load event trace for a run."""
        if not self._pool:
            raise RuntimeError("Not connected")

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT payload FROM events
                WHERE run_id = $1
                ORDER BY timestamp ASC
                """,
                run_id,
            )

            if not rows:
                return None

            return [json.loads(row["payload"]) for row in rows]

    async def list_runs(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """List available runs."""
        if not self._pool:
            raise RuntimeError("Not connected")

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT run_id, created_at, completed_at, source, event_count, metadata
                FROM runs
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )

            return [
                {
                    "run_id": row["run_id"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "completed_at": row["completed_at"].isoformat() if row["completed_at"] else None,
                    "source": row["source"],
                    "event_count": row["event_count"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                }
                for row in rows
            ]

    async def delete_run(self, run_id: str) -> bool:
        """Delete a run and its trace."""
        if not self._pool:
            raise RuntimeError("Not connected")

        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM runs WHERE run_id = $1",
                run_id,
            )
            return "DELETE 1" in result


class PostgresAuditStore(AuditStore):
    """PostgreSQL-backed audit log storage."""

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def log(
        self,
        actor: str,
        action: str,
        resource: str,
        outcome: str,
        metadata: dict | None = None,
    ) -> str:
        """Log an audit entry."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO audit_logs (actor, action, resource, outcome, metadata)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                actor,
                action,
                resource,
                outcome,
                json.dumps(metadata or {}),
            )
            return str(row["id"])

    async def query(
        self,
        actor: str | None = None,
        action: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query audit logs."""
        conditions = []
        params = []
        param_idx = 1

        if actor:
            conditions.append(f"actor = ${param_idx}")
            params.append(actor)
            param_idx += 1

        if action:
            conditions.append(f"action = ${param_idx}")
            params.append(action)
            param_idx += 1

        if start_time:
            conditions.append(f"timestamp >= ${param_idx}")
            params.append(start_time)
            param_idx += 1

        if end_time:
            conditions.append(f"timestamp <= ${param_idx}")
            params.append(end_time)
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, timestamp, actor, action, resource, outcome, metadata
                FROM audit_logs
                WHERE {where_clause}
                ORDER BY timestamp DESC
                LIMIT ${param_idx}
                """,
                *params,
            )

            return [
                {
                    "id": row["id"],
                    "timestamp": row["timestamp"].isoformat(),
                    "actor": row["actor"],
                    "action": row["action"],
                    "resource": row["resource"],
                    "outcome": row["outcome"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                }
                for row in rows
            ]
