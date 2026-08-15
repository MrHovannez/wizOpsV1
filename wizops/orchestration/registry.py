from __future__ import annotations

from collections.abc import Iterator

from wizops.events.archive import ArchiveStore
from wizops.orchestration.factories import FACTORIES
from wizops.domain import iter_sources


def collector_jobs(
    store: ArchiveStore,
) -> Iterator[tuple[object, dict]]:
    for source in iter_sources():
        builder = FACTORIES.get(type(source))

        if builder is None:
            raise ValueError(
                f"No factory registered for source type: {type(source).__name__}"
            )

        yield builder(store, source)
