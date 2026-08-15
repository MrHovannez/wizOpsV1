from wizops.config import DATA_DIR, LOG_DIR
from wizops.platform.linux.linux_platform import LinuxPlatform
from wizops.events.archive import ArchiveStore
from wizops.infrastructure.system import probe_system
from pathlib import Path

from wizops.application.models import (
    SituationMetrics,
    CapacityStatus,
    HealthStatus,
    ServicesStatus,
    CollectionStatus,
    DatabaseStatus,
    SeverityStatus,
    SystemStatus,
    LatestStatus,
)


def _size(path: Path) -> int:
    total = 0

    if not path.exists():
        return 0

    for p in path.rglob("*"):
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass

    return total

class SituationService:

    def __init__(
        self,
        platform: LinuxPlatform,
        store: ArchiveStore,
        db_path: Path,
    ):
        self.platform = platform
        self.store = store
        self.db_path = Path(db_path)


    def metrics(self) -> SituationMetrics:
        counts = self.store.severity_counts()

        fatal = counts.get("FATAL", 0)
        errors = counts.get("ERROR", 0) + counts.get("FATAL", 0)
        warnings = counts.get("WARN", 0)
        info = counts.get("INFO", 0)
        total = sum(counts.values())

        return SituationMetrics(
            fatal=fatal,
            errors=errors,
            warnings=warnings,
            info=info,
            total=total,
        )



    def capacity(self) -> CapacityStatus:
        storages = self.platform.storage.snapshot()

        matching = [
            storage
            for storage in storages
            if DATA_DIR == Path(storage.mountpoint)
            or DATA_DIR.is_relative_to(storage.mountpoint)
        ]

        if not matching:
            raise RuntimeError(
                f"Could not determine filesystem for WizardOps data: {DATA_DIR}"
            )

        disk = max(
            matching,
            key=lambda storage: len(Path(storage.mountpoint).parts),
        )

        log_size = _size(LOG_DIR)

        db_size = (
            self.db_path.stat().st_size
            if self.db_path.exists()
            else 0
        )

        return CapacityStatus(
            storage=disk,
            log_size=log_size,
            database_size=db_size,
        )


    def health(self) -> HealthStatus:
        bounds = self.store.event_bounds()
        first_ts = bounds[0]
        last_ts = bounds[1]
        lifetime_total = bounds[2]

        counts24 = self.store.severity_counts_last_24h()

        err24 = counts24.get("ERROR", 0)
        warn24 = counts24.get("WARN", 0)
        fatal24 = counts24.get("FATAL", 0)
        info24 = counts24.get("INFO", 0)

        total24 = sum(counts24.values())
        attention24 = err24 + warn24 + fatal24

        hourly_sev = self.store.hourly_severity_counts()

        sev_series = {
             "ERROR": [0] * 24,
            "WARN": [0] * 24,
            "FATAL": [0] * 24,
            "INFO": [0] * 24,
         }

        for hour, severity, count in hourly_sev:
             if hour is not None and severity in sev_series:
                 sev_series[severity][int(hour)] = int(count)

        return HealthStatus(
            err24=err24,
            warn24=warn24,
            fatal24=fatal24,
            info24=info24,
            attention24=attention24,
            total24=total24,
            lifetime_total=lifetime_total,
            first_ts=first_ts,
            last_ts=last_ts,
             sev_series=sev_series,
        )


    def services(self) -> ServicesStatus:
        svcrows = self.store.top_services_last_24h()

        distinct = self.store.distinct_services_last_24h()

        counts24 = self.store.severity_counts_last_24h()
        total24 = sum(counts24.values())

        return ServicesStatus(
            services=svcrows,
            total24=total24,
            distinct_services=distinct,
        )


    def collection(self) -> CollectionStatus:
        state_rows = self.store.list_states()
        bounds = self.store.event_bounds()

        if bounds:
            first_ts = bounds[0] or ""
            last_ts = bounds[1] or ""
        else:
            first_ts = ""
            last_ts = ""

        latest_state = (
            (state_rows[0]["updated_at"] or "")
            .replace("Z", "")
            .replace("T", " ")[:19]
            if state_rows else "—"
        )

        return CollectionStatus(
            collectors_active=len(state_rows),
            latest_state=latest_state,
            first_ts=first_ts,
            last_ts=last_ts,
        )


    def database(self) -> DatabaseStatus:
        bounds = self.store.event_bounds()

        if bounds:
            first_ts = bounds[0] or ""
            last_ts = bounds[1] or ""
            lifetime_total = bounds[2] or 0
        else:
            first_ts = ""
            last_ts = ""
            lifetime_total = 0

        database_size = (
            self.db_path.stat().st_size
            if self.db_path.exists()
            else 0
        )

        return DatabaseStatus(
            lifetime_total=lifetime_total,
            first_ts=first_ts,
            last_ts=last_ts,
            database_size=database_size,
        )



    def severity(self) -> SeverityStatus:
        counts24 = self.store.severity_counts_last_24h()
        previous = self.store.previous_severity_counts()
        bucket_rows = self.store.severity_buckets_last_24h()
        chart = {
            "ERROR": [0] * 48,
            "WARN": [0] * 48,
            "FATAL": [0] * 48,
        }
        for bucket, severity, count in bucket_rows:
            if (
                bucket is not None
                and severity in chart
                and 0 <= int(bucket) < 48
            ):
                chart[severity][int(bucket)] = int(count)
        stats = []
        for severity in ("ERROR", "WARN", "FATAL"):
            current = counts24.get(severity, 0)
            previous_count = previous.get(severity, 0)
            delta = (
                (current - previous_count) / previous_count * 100
                if previous_count
                else (100.0 if current else 0.0)
            )
            arrow = (
                "↑"
                if delta > 0
                else "↓"
                if delta < 0
                else "→"
            )
            stats.append(
                f"{severity} {current:,} {arrow}{abs(delta):.0f}%"
            )
        return SeverityStatus(
            counts24=counts24,
            previous=previous,
            chart=chart,
            stats=stats,
        )



    def system(self) -> SystemStatus:
        collection = self.collection()

        return probe_system(
            collectors_active=collection.collectors_active,
        )


    def latest(self) -> LatestStatus:
        return LatestStatus(
            event=self.store.latest_attention(),
        )
