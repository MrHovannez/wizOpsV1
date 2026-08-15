from dataclasses import dataclass


@dataclass(frozen=True)
class LinuxService:
    unit: str
    description: str
    load: str
    active: str
    substate: str

    @property
    def healthy(self) -> bool:
        return self.active == "active"

    @property
    def unit_name(self) -> str:
        return self.unit.removesuffix(".service")


@dataclass(frozen=True)
class LinuxJournalEntry:
    cursor: str
    timestamp: int
    hostname: str
    unit: str
    identifier: str
    priority: int
    message: str


@dataclass(slots=True)
class JournalQuery:
    limit: int = 100
    unit: str | None = None
    since: str | None = None
    until: str | None = None



