from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Iterable
from .event import Event

SCHEMA_VERSION = 2
SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  timestamp TEXT NOT NULL,
  service TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('TRACE','DEBUG','INFO','WARN','ERROR','FATAL')),
  category TEXT NOT NULL,
  message TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source TEXT NOT NULL,
  raw_event TEXT NOT NULL,
  source_position TEXT,
  pid INTEGER,
  correlation_id TEXT,
  model TEXT,
  request_id TEXT,
  tool_call_id TEXT,
  session_id TEXT,
  fingerprint TEXT NOT NULL UNIQUE,
  ingested_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_service_timestamp ON events(service, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_severity_timestamp ON events(severity, timestamp);
CREATE TABLE IF NOT EXISTS collector_state (
  collector_id TEXT NOT NULL,
  source TEXT NOT NULL,
  inode INTEGER,
  byte_offset INTEGER NOT NULL DEFAULT 0,
  last_timestamp TEXT,
  cursor TEXT,
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  PRIMARY KEY (collector_id, source)
);
"""

class ArchiveStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row

        from .collector_state import CollectorStateStore
        self.collector_state = CollectorStateStore(self.db)

    def close(self): self.db.close()
    def init_schema(self):
        with self.db:
            self.db.executescript(SCHEMA)
            row = self.db.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
            if row is None: self.db.execute("INSERT INTO schema_version(version) VALUES (?)", (SCHEMA_VERSION,))
            elif row[0] != SCHEMA_VERSION: raise RuntimeError(f"Unsupported schema version {row[0]}")
    def _fields(self, event: Event):
        return (event.timestamp,event.service,event.severity,event.category,event.message,event.source_type,event.source,event.raw_event,event.source_position,event.pid,event.correlation_id,event.model,event.request_id,event.tool_call_id,event.session_id,event.fingerprint)
    def add(self, event: Event) -> bool:
        fields = self._fields(event)
        with self.db:
            cur = self.db.execute("INSERT OR IGNORE INTO events(timestamp,service,severity,category,message,source_type,source,raw_event,source_position,pid,correlation_id,model,request_id,tool_call_id,session_id,fingerprint) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", fields)
        return cur.rowcount == 1
    def add_many(self, events: Iterable[Event]) -> int:
        sql = "INSERT OR IGNORE INTO events(timestamp,service,severity,category,message,source_type,source,raw_event,source_position,pid,correlation_id,model,request_id,tool_call_id,session_id,fingerprint) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        before = self.db.total_changes
        with self.db:
            self.db.executemany(sql, (self._fields(event) for event in events))
        return self.db.total_changes - before
    def query(self, *, service=None, severity=None, search=None, limit=100):
        clauses=[]; args=[]
        if service: clauses.append("service=?"); args.append(service)
        if severity: clauses.append("severity=?"); args.append(severity)
        if search: clauses.append("(message LIKE ? OR raw_event LIKE ? OR category LIKE ? OR COALESCE(model,'') LIKE ? OR COALESCE(request_id,'') LIKE ?)"); args.extend([f"%{search}%"]*5)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        args.append(limit)
        return self.db.execute("SELECT * FROM events"+where+" ORDER BY timestamp DESC,id DESC LIMIT ?", args).fetchall()
    def count(self): return self.db.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def list_events(self):
        return self.db.execute(
            """
            SELECT *
            FROM events
            ORDER BY timestamp DESC, id DESC
            """
        ).fetchall()

    def distinct_services(self):
        return [
            row[0]
            for row in self.db.execute(
                """
                SELECT DISTINCT service
                FROM events
                WHERE service IS NOT NULL
                 AND service != ''
                ORDER BY service
                """
            ).fetchall()
        ]


    def severity_counts(self):
        return dict(
            self.db.execute(
                """
                SELECT severity, COUNT(*)
                FROM events
                GROUP BY severity
                """
            ).fetchall()
        )

    def event_bounds(self):
        return self.db.execute(
            """
            SELECT
                MIN(timestamp),
                MAX(timestamp),
                COUNT(*)
            FROM events
            """
        ).fetchone()

    def list_states(self):
        return self.db.execute(
            """
            SELECT
                collector_id,
                source,
                last_timestamp,
                updated_at
            FROM collector_state
            ORDER BY updated_at DESC
            """
        ).fetchall()

    def severity_counts_last_24h(self):
        return dict(
            self.db.execute(
                """
                SELECT severity, COUNT(*)
                FROM events
                WHERE timestamp >= datetime('now', '-24 hours')
                GROUP BY severity
                """
            ).fetchall()
        )

    def hourly_severity_counts(self):
        return self.db.execute(
            """
            SELECT
                strftime('%H', timestamp) AS hour,
                severity,
                COUNT(*) AS count
            FROM events
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY hour, severity
            ORDER BY hour
            """
        ).fetchall()

    def activity_last_24h(self):
        return self.db.execute(
            """
            SELECT
                CAST(
                    (julianday(timestamp) - julianday('now', '-24 hours')) * 96
                    AS INTEGER
                ) AS bucket,
                COUNT(*) AS count
            FROM events
            WHERE julianday(timestamp) >= julianday('now', '-24 hours')
              AND julianday(timestamp) <= julianday('now')
            GROUP BY bucket
            ORDER BY bucket
            """
        ).fetchall()

    def top_services_last_24h(self, limit: int = 10):
        return self.db.execute(
            """
            SELECT
                service,
                COUNT(*) AS count
            FROM events
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY service
            ORDER BY count DESC
            LIMIT 10
            """
        ).fetchall()

    def distinct_services_last_24h(self):
        return self.db.execute(
            """
            SELECT COUNT(DISTINCT service)
            FROM events
            WHERE timestamp >= datetime('now', '-24 hours')
            """
        ).fetchone()[0]

    def severity_buckets_last_24h(self):
        return self.db.execute(
            """
            SELECT
                CAST(
                    (julianday(timestamp) - julianday('now', '-24 hours')) * 48
                    AS INTEGER
                ) AS bucket,
                severity,
                COUNT(*) AS count
            FROM events
            WHERE julianday(timestamp) >= julianday('now', '-24 hours')
              AND julianday(timestamp) <= julianday('now')
              AND severity IN ('ERROR', 'WARN', 'FATAL')
            GROUP BY bucket, severity
            ORDER BY bucket
            """
        ).fetchall()

    def previous_severity_counts(self):
        return dict(
            self.db.execute(
                """
                SELECT
                    severity,
                    COUNT(*)
                FROM events
                WHERE julianday(timestamp) >= julianday('now', '-48 hours')
                  AND julianday(timestamp) < julianday('now', '-24 hours')
                GROUP BY severity
                """
            ).fetchall()
        )

    def search_events(
        self,
        where: str,
        params: tuple | list = (),
    ):
        return self.db.execute(
            """
            SELECT *
            FROM events
            """ + where + """
            ORDER BY timestamp DESC, id DESC
            LIMIT 1000
            """,
            params,
        ).fetchall()

    def pattern_summary(self, service: str, message: str):
        return self.db.execute(
            """
            SELECT
                MIN(timestamp),
                MAX(timestamp),
                COUNT(*)
            FROM events
            WHERE service = ?
              AND substr(message, 1, 80) = substr(?, 1, 80)
            """,
            (service, message),
        ).fetchone()

    def related_events(
        self,
        event_id: int,
        service: str,
        category: str | None,
        request_id: str | None,
        model: str | None,
    ):
        return self.db.execute(
            """
            SELECT
                id,
                timestamp,
                severity,
                service,
                message,
                (
                    CASE
                        WHEN request_id IS NOT NULL
                         AND request_id = ? THEN 100
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN model IS NOT NULL
                         AND model = ? THEN 40
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN category IS NOT NULL
                         AND category = ? THEN 30
                        ELSE 0
                    END
                    +
                    CASE
                        WHEN service = ? THEN 10
                        ELSE 0
                    END
                ) AS relation_score
            FROM events
            WHERE id != ?
              AND (
                    service = ?
                 OR (category IS NOT NULL AND category = ?)
                 OR (request_id IS NOT NULL AND request_id = ?)
                 OR (model IS NOT NULL AND model = ?)
              )
            ORDER BY relation_score DESC, ABS(id - ?) ASC
            LIMIT 12
            """,
            (
                request_id,
                model,
                category,
                service,
                event_id,
                service,
                category,
                request_id,
                model,
                event_id,
            ),
        ).fetchall()

    def latest_attention(self):
        return self.db.execute(
            """
            SELECT
                id,
                timestamp,
                severity,
                service,
                message
            FROM events
            WHERE severity IN ('WARN', 'ERROR', 'FATAL')
            ORDER BY timestamp DESC, id DESC
            LIMIT 1
            """
        ).fetchone()
