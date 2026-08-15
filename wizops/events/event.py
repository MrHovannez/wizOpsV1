from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib

@dataclass(frozen=True)
class Event:
    timestamp: str
    service: str
    severity: str
    category: str
    message: str
    source_type: str
    source: str
    raw_event: str
    source_position: str | None = None
    pid: int | None = None
    correlation_id: str | None = None
    model: str | None = None
    request_id: str | None = None
    tool_call_id: str | None = None
    session_id: str | None = None

    @property
    def fingerprint(self) -> str:
        identity = self.source_position or self.timestamp
        payload = "\0".join((self.source_type, self.source, identity, self.raw_event))
        return hashlib.sha256(payload.encode("utf-8", errors="surrogateescape")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
