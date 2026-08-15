from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from wizops.events.parsers.file_logs import parse_file_log_record
from wizops.events.archive import ArchiveStore


class FileLogCollector:
    collector_id = "file-log-v1"

    def __init__(self, store: ArchiveStore):
        self.store = store

    def collect(self, *, service: str, path: Path) -> dict:
        path = Path(path)
        stat = path.stat()
        source = str(path.resolve())

        state = self.store.collector_state.get_state(self.collector_id,source,)

        offset = 0
        if (
            state
            and state["inode"] == stat.st_ino
            and 0 <= state["byte_offset"] <= stat.st_size
        ):
            offset = state["byte_offset"]

        fallback = (
            datetime.fromtimestamp(stat.st_mtime, timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

        seen = 0
        inserted = 0
        last_ts = state["last_timestamp"] if state else None

        with path.open("rb") as handle:
            handle.seek(offset)

            while True:
                record_offset = handle.tell()
                raw = handle.readline()

                if not raw:
                    break

                seen += 1

                line = raw.decode("utf-8", errors="replace")
                source_position = str(record_offset)

                event = parse_file_log_record(
                    line,
                    service=service,
                    source=source,
                    fallback_timestamp=fallback,
                    source_position=source_position,
                )

                inserted += int(self.store.add(event))
                last_ts = event.timestamp

            new_offset = handle.tell()

        self.store.collector_state.set_state(
            self.collector_id,
            source,
            stat.st_ino,
            new_offset,
            last_ts,
        )

        return {
            "seen": seen,
            "inserted": inserted,
            "deduplicated": seen - inserted,
            "offset": new_offset,
            "source": source,
        }
