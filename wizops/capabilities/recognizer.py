from __future__ import annotations

from abc import ABC, abstractmethod

from wizops.inventory.models import (
    Capability,
    InventorySnapshot,
)


class CapabilityRecognizer(ABC):

    @abstractmethod
    def recognize(
        self,
        inventory: InventorySnapshot,
    ) -> Capability | None:
        ...
