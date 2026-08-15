from __future__ import annotations

from wizops.orchestration.coordinator import OrchestrationCoordinator


def refresh(store):
    return OrchestrationCoordinator(store).collect()
