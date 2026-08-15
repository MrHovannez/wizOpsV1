from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter

from wizops.events.archive import ArchiveStore
from wizops.orchestration.registry import collector_jobs

@dataclass(slots=True)
class OrchestrationResult:
    seen: int = 0
    inserted: int = 0
    deduplicated: int = 0
    elapsed_time: float = 0.0
    errors: list[str] = field(default_factory=list)


class OrchestrationCoordinator:
    def __init__(self, store: ArchiveStore):
        self.store = store

    def collect(self) -> OrchestrationResult:
        result = OrchestrationResult()

        start = perf_counter()

        jobs = list(collector_jobs(self.store))
        total = len(jobs)

        for index, (collector, kwargs) in enumerate(jobs, start=1):
            source = kwargs.get("unit", kwargs["service"])

            print(f"[{index}/{total}] {source}")

            try:
                inserted = 0

                for event in collector.collect(**kwargs):
                    result.seen += 1

                    self.store.add(event)

                    inserted += 1
                    result.inserted += 1

                print(f"    ✓ Finished {source}")
                print(
                    f"    seen={result.seen} "
                    f"inserted={inserted}"
                )

            except Exception as exc:
                print(f"    ERROR: {exc}")
                result.errors.append(str(exc))

        result.elapsed_time = perf_counter() - start

        print()
        print("=" * 60)
        print("Collection complete")
        print("=" * 60)
        print(f"Seen          : {result.seen}")
        print(f"Inserted      : {result.inserted}")
        print(f"Deduplicated  : {result.deduplicated}")
        print(f"Errors        : {len(result.errors)}")
        print(f"Elapsed       : {result.elapsed_time:.2f}s")
        print()

        return result
