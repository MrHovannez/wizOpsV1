from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone

from wizops.events.event import Event
from wizops.platform.linux.models import LinuxJournalEntry


PRIORITY_TO_SEVERITY: dict[int, str] = {
    0: "FATAL",
    1: "FATAL",
    2: "FATAL",
    3: "ERROR",
    4: "WARN",
    5: "INFO",
    6: "INFO",
    7: "DEBUG",
}


def journal_entry_to_event(entry: LinuxJournalEntry) -> Event:
    timestamp = (
        datetime.fromtimestamp(
            entry.timestamp / 1_000_000,
            tz=timezone.utc,
        )
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )

    return Event(
        timestamp=timestamp,
        service=entry.unit,
        severity=PRIORITY_TO_SEVERITY.get(entry.priority, "info"),
        category="journal",
        message=entry.message,
        source_type="journal",
        source=entry.hostname,
        raw_event=json.dumps(asdict(entry), sort_keys=True),
    )
