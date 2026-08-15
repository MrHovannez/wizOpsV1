from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CollectorRequest:
    unit: str | None = None
    since: str | None = None
    until: str | None = None
    cursor: str | None = None
    limit: int | None = None


@dataclass(slots=True)
class CollectorPage:
    entries: list
    next_cursor: str | None = None
