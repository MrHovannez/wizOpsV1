from __future__ import annotations

import sqlite3


class CollectorStateStore:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def get_state(
        self,
        collector_id: str,
        source: str,
    ):
        return self.db.execute(
            """
            SELECT *
            FROM collector_state
            WHERE collector_id = ?
              AND source = ?
            """,
            (collector_id, source),
        ).fetchone()

    def set_state(
        self,
        collector_id: str,
        source: str,
        inode: int,
        byte_offset: int,
        last_timestamp: str | None,
        cursor: str | None = None,
    ):
        with self.db:
            self.db.execute(
                """
                INSERT INTO collector_state(
                    collector_id,
                    source,
                    inode,
                    byte_offset,
                    last_timestamp,
                    cursor
                )
                VALUES (?,?,?,?,?,?)
                ON CONFLICT(collector_id, source)
                DO UPDATE SET
                    inode = excluded.inode,
                    byte_offset = excluded.byte_offset,
                    last_timestamp = excluded.last_timestamp,
                    cursor = excluded.cursor,
                    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')
                """,
                (
                    collector_id,
                    source,
                    inode,
                    byte_offset,
                    last_timestamp,
                    cursor,
                ),
            )

    def list_states(self):
        return self.db.execute(
            """
            SELECT
                collector_id,
                source,
                updated_at
            FROM collector_state
            ORDER BY collector_id, source
            """
        ).fetchall()

