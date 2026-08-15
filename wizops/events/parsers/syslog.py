from __future__ import annotations

import re
from datetime import datetime, timezone

from wizops.events.event import Event, utc_now_iso
from wizops.events.severity import parse_severity

SyslogRecord = str


_SYSLOG_PATTERN = re.compile(
    r"^(?P<month>[A-Z][a-z]{2})\s+"
    r"(?P<day>\d{1,2})\s+"
    r"(?P<time>\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<service>[^:\[]+)"
    r"(?:\[(?P<pid>\d+)\])?:\s*"
    r"(?P<message>.*)$"
)

_MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def _build_timestamp(month: str, day: str, clock: str) -> str:
    now = datetime.now(timezone.utc)

    dt = datetime(
        year=now.year,
        month=_MONTHS[month],
        day=int(day),
        hour=int(clock[0:2]),
        minute=int(clock[3:5]),
        second=int(clock[6:8]),
        tzinfo=timezone.utc,
    )

    return (
        dt.isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def parse_syslog_record(
    record: SyslogRecord,
    *,
    service: str,
    source: str,
    source_position: str | None = None,
) -> Event:

    raw = record.rstrip("\r\n")

    match = _SYSLOG_PATTERN.match(raw)

    if match:
        timestamp = _build_timestamp(
            match.group("month"),
            match.group("day"),
            match.group("time"),
        )

        message = match.group("message")
        pid = match.group("pid")

    else:
        timestamp = utc_now_iso()
        message = raw
        pid = None

    severity = parse_severity(message)

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
        source_type="syslog",
        source=source,
        raw_event=raw,
        source_position=source_position,
        pid=pid,
    )
