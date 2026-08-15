from __future__ import annotations

from wizops.inventory.models import (
    CapabilityInventory,
)

from .registry import recognizers


class CapabilityCoordinator:

    def recognize(
        self,
        snapshot,
    ) -> CapabilityInventory:

        capabilities = []

        for recognizer in recognizers():

            capability = recognizer.recognize(snapshot)

            if capability is not None:
                capabilities.append(capability)

        return CapabilityInventory(
            capabilities=capabilities,
        )
