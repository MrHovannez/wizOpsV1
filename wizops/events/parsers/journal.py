from __future__ import annotations

from datetime import datetime, timezone

from wizops.events.event import Event
from wizops.events.severity import parse_severity


PRIORITY_MAP = {
    "0": "FATAL",
    "1": "FATAL",
    "2": "FATAL",
    "3": "ERROR",
    "4": "WARN",
    "5": "INFO",
    "6": "INFO",
    "7": "DEBUG",
}

JournalRecord = dict[str, object]


def parse_journal_record(
    record: JournalRecord,
    *,
    service: str,
    source: str,
) -> Event:
    message = str(record.get("MESSAGE", ""))

    micros = int(record["__REALTIME_TIMESTAMP"])

    timestamp = (
        datetime.fromtimestamp(
            micros / 1_000_000,
            tz=timezone.utc,
        )
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )

    severity = parse_severity(message)

    if severity == "INFO":
        severity = PRIORITY_MAP.get(
            str(record.get("PRIORITY", "6")),
            "INFO",
        )

    category = (
        "error"
        if severity in {"ERROR", "FATAL"}
        else "warning"
        if severity == "WARN"
        else "log"
    )

    return Event(
        timestamp=timestamp,
        service=service,
        severity=severity,
        category=category,
        message=message,
        source_type="journal",
        source=source,
        raw_event=message,
        source_position=str(record.get("__CURSOR", "")),
        pid=str(record.get("_PID"))
        if record.get("_PID") is not None
        else None,
    )
