from __future__ import annotations

from wizops.inventory.models import (
    Capability,
    CapabilityImplementation,
    CapabilityKind,
    InventorySnapshot,
)

from ..recognizer import CapabilityRecognizer


class RemoteAccessRecognizer(CapabilityRecognizer):

    def recognize(
        self,
        inventory: InventorySnapshot,
    ) -> Capability | None:

        for service in inventory.services.services:

            if (
                service.name == "sshd"
                and service.state == "running"
            ):
                return Capability(
                    kind=CapabilityKind.REMOTE_ACCESS,
                    implementations=[
                        CapabilityImplementation(
                            name="OpenSSH",
                        )
                    ],
                )

        return None
