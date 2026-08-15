from __future__ import annotations

from wizops.inventory.models import (
    Capability,
    CapabilityImplementation,
    CapabilityKind,
    InventorySnapshot,
)

from ..recognizer import CapabilityRecognizer


class PackageManagerRecognizer(CapabilityRecognizer):

    def recognize(
        self,
        inventory: InventorySnapshot,
    ) -> Capability | None:

        if not inventory.package_managers.managers:
            return None

        return Capability(
            kind=CapabilityKind.PACKAGE_MANAGER,
            implementations=[
                CapabilityImplementation(
                    name=manager.name,
                )
                for manager in inventory.package_managers.managers
            ],
        )
