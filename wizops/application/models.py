from dataclasses import dataclass
from pathlib import Path

from wizops.inventory.models import (
    Cpu,
    Memory,
    NetworkInventory,
    Storage,
)


@dataclass(frozen=True)
class SystemOverview:
    cpu: Cpu
    memory: Memory
    storage: Storage
    network: NetworkInventory


@dataclass(frozen=True)
class SituationMetrics:
    errors: int
    warnings: int
    fatal: int
    info: int
    total: int


@dataclass(frozen=True)
class CapacityStatus:
    storage: Storage

    log_size: int
    database_size: int


@dataclass(frozen=True)
class HealthStatus:
    err24: int
    warn24: int
    fatal24: int
    info24: int
    attention24: int
    total24: int
    lifetime_total: int
    first_ts: str | None
    last_ts: str | None
    sev_series: dict[str, list[int]]


@dataclass(frozen=True)
class ServicesStatus:
    services: list[tuple[str, int]]
    total24: int
    distinct_services: int


@dataclass(frozen=True)
class CollectionStatus:
    collectors_active: int
    latest_state: str
    first_ts: str
    last_ts: str


@dataclass(frozen=True)
class DatabaseStatus:
    lifetime_total: int
    first_ts: str
    last_ts: str
    database_size: int


@dataclass(frozen=True)
class SeverityStatus:
    counts24: dict[str, int]
    previous: dict[str, int]
    chart: dict[str, list[int]]
    stats: list[str]


@dataclass(frozen=True)
class SystemStatus:
    load1: float
    mem_total: int
    mem_avail: int
    gpu_used: float | None
    gpu_total: float | None
    disk_used: int
    disk_total: int
    hostname: str
    container_count: int
    loaded_models: int
    collectors_active: int


@dataclass(frozen=True)
class EventQuery:
    service: str | None = None
    severity: str | None = None
    search: str | None = None
    time_window: str = "24h"


@dataclass(frozen=True)
class EventsResult:
    events: list


@dataclass(frozen=True)
class LatestStatus:
    event: dict | None




@dataclass(frozen=True)
class InspectionResult:
    ...


@dataclass(frozen=True)
class ExportRequest:
    ...


@dataclass(frozen=True)
class ExportResult:
    success: bool
    message: str
    path: Path | None

