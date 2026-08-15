from __future__ import annotations

from datetime import datetime, timezone
import re

from wizops.events.event import Event, utc_now_iso
from wizops.events.severity import parse_severity


FileLogRecord = str


_TS_PATTERNS = (
    re.compile(
        r"^(?P<ts>\d{4}-\d{2}-\d{2}[T ][0-9:.]+(?:Z|[+-]\d{2}:?\d{2})?)\s*(?P<rest>.*)$"
    ),
    re.compile(
        r"^\[(?P<ts>\d{4}-\d{2}-\d{2}[T ][0-9:.]+(?:Z|[+-]\d{2}:?\d{2})?)\]\s*(?P<rest>.*)$"
    ),
)


def _normalize_ts(value: str | None, fallback: str | None) -> str:
    if not value:
        return fallback or utc_now_iso()

    value = value.replace(" ", "T", 1)

    if value.endswith("Z"):
        return value

    try:
        parsed = datetime.fromisoformat(value)

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return (
            parsed.astimezone(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )

    except ValueError:
        return fallback or utc_now_iso()


def parse_file_log_record(
    record: FileLogRecord,
    *,
    service: str,
    source: str,
    fallback_timestamp: str | None = None,
    source_position: str | None = None,
) -> Event:

    raw = record.rstrip("\r\n")

    timestamp = None
    message = raw

    for pattern in _TS_PATTERNS:
        match = pattern.match(raw)

        if match:
            timestamp = match.group("ts")
            message = match.group("rest") or raw
            break

    severity = parse_severity(message)

    category = (
        "error"
        if severity in {"ERROR", "FATAL"}
        else "warning"
        if severity == "WARN"
        else "log"
    )

    return Event(
        timestamp=_normalize_ts(timestamp, fallback_timestamp),
        service=service,
        severity=severity,
        category=category,
        message=message,
        source_type="file",
        source=source,
        raw_event=raw,
        source_position=source_position,
    )
