from __future__ import annotations

from wizops.inventory.models import (
    Capability,
    CapabilityImplementation,
    CapabilityKind,
    InventorySnapshot,
)

from ..recognizer import CapabilityRecognizer


class SchedulerRecognizer(CapabilityRecognizer):

    def recognize(
        self,
        inventory: InventorySnapshot,
    ) -> Capability | None:

        implementations = []

        for service in inventory.services.services:

            if (
                service.state != "running"
            ):
                continue

            if service.name == "systemd":
                implementations.append(
                    CapabilityImplementation(
                        name="systemd",
                    )
                )

            elif service.name in {
                "cron",
                "crond",
            }:
                implementations.append(
                    CapabilityImplementation(
                        name="cron",
                    )
                )

        if not implementations:
            return None

        return Capability(
            kind=CapabilityKind.SCHEDULER,
            implementations=implementations,
        )
