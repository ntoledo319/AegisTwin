"""
Event persistence layer using SQLite.

Stores all events published through the EventBus for audit, replay, and analysis.
Thread-safe with proper connection handling.
"""

from __future__ import annotations
from pathlib import Path
import sqlite3
import time
import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)


class EventStore:
    """
    Thread-safe event storage using SQLite.
    
    Each thread gets its own connection to avoid threading issues.
    """
    
    def __init__(self, db_path: str | Path):
        """
        Initialize event store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = str(db_path)
        self._local = threading.local()
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=10.0
            )
            # Enable WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode=WAL")
        return self._local.connection
    
    @contextmanager
    def _transaction(self):
        """Context manager for database transactions."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            with self._transaction() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id TEXT PRIMARY KEY,
                        ts REAL NOT NULL,
                        topic TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        qos INTEGER DEFAULT 0,
                        key TEXT
                    )
                """)
                
                # Indexes for common queries
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_ts 
                    ON events(ts DESC)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_topic 
                    ON events(topic)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_key 
                    ON events(key) WHERE key IS NOT NULL
                """)
            
            logger.info(f"Event store initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize event store: {e}")
            raise
    
    def persist(
        self,
        topic: str,
        payload: dict,
        qos: int = 0,
        key: Optional[str] = None
    ) -> str:
        """
        Persist an event to the database.
        
        Args:
            topic: Event topic
            payload: Event data
            qos: Quality of service level
            key: Optional key for event deduplication/grouping
            
        Returns:
            Event ID
        """
        event_id = str(uuid.uuid4())
        
        try:
            with self._transaction() as conn:
                conn.execute(
                    "INSERT INTO events (id, ts, topic, payload, qos, key) VALUES (?, ?, ?, ?, ?, ?)",
                    (event_id, time.time(), topic, json.dumps(payload), qos, key)
                )
            
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to persist event {event_id}: {e}")
            raise
    
    def query(
        self,
        topic_pattern: Optional[str] = None,
        since_ts: Optional[float] = None,
        until_ts: Optional[float] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query events from the database.
        
        Args:
            topic_pattern: SQL LIKE pattern for topic filtering
            since_ts: Minimum timestamp
            until_ts: Maximum timestamp
            limit: Maximum number of results
            
        Returns:
            List of event dictionaries
        """
        query = "SELECT id, ts, topic, payload, qos, key FROM events WHERE 1=1"
        params = []
        
        if topic_pattern:
            query += " AND topic LIKE ?"
            params.append(topic_pattern)
        
        if since_ts is not None:
            query += " AND ts >= ?"
            params.append(since_ts)
        
        if until_ts is not None:
            query += " AND ts <= ?"
            params.append(until_ts)
        
        query += " ORDER BY ts DESC LIMIT ?"
        params.append(limit)
        
        try:
            conn = self._get_connection()
            cursor = conn.execute(query, params)
            
            events = []
            for row in cursor.fetchall():
                events.append({
                    "id": row[0],
                    "ts": row[1],
                    "topic": row[2],
                    "payload": json.loads(row[3]),
                    "qos": row[4],
                    "key": row[5]
                })
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to query events: {e}")
            return []
    
    def count(self, topic_pattern: Optional[str] = None) -> int:
        """
        Count events matching criteria.
        
        Args:
            topic_pattern: SQL LIKE pattern for topic filtering
            
        Returns:
            Event count
        """
        query = "SELECT COUNT(*) FROM events"
        params = []
        
        if topic_pattern:
            query += " WHERE topic LIKE ?"
            params.append(topic_pattern)
        
        try:
            conn = self._get_connection()
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
            
        except Exception as e:
            logger.error(f"Failed to count events: {e}")
            return 0
    
    def cleanup(self, older_than_ts: float) -> int:
        """
        Delete events older than given timestamp.
        
        Args:
            older_than_ts: Timestamp threshold
            
        Returns:
            Number of events deleted
        """
        try:
            with self._transaction() as conn:
                cursor = conn.execute(
                    "DELETE FROM events WHERE ts < ?",
                    (older_than_ts,)
                )
                deleted = cursor.rowcount
            
            logger.info(f"Cleaned up {deleted} old events")
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to cleanup events: {e}")
            return 0
    
    def close(self) -> None:
        """Close database connections."""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()


# Legacy API for backward compatibility
def init_event_store(db_path: str | Path) -> EventStore:
    """Initialize event store (legacy API)."""
    return EventStore(db_path)


def persist_event(db_path: str | Path, topic: str, payload: dict) -> None:
    """Persist event (legacy API - creates new connection each time, not recommended)."""
    store = EventStore(db_path)
    store.persist(topic, payload)
    store.close()
