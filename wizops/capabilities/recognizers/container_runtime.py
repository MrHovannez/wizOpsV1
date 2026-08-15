from __future__ import annotations

from wizops.inventory.models import (
    Capability,
    CapabilityImplementation,
    CapabilityKind,
    InventorySnapshot,
)

from ..recognizer import CapabilityRecognizer


IMPLEMENTATIONS = {
    "docker": "Docker",
    "podman": "Podman",
    "containerd": "containerd",
    "cri-o": "CRI-O",
}


class ContainerRuntimeRecognizer(CapabilityRecognizer):

    def recognize(
        self,
        inventory: InventorySnapshot,
    ) -> Capability | None:

        implementations: list[CapabilityImplementation] = []

        for service in inventory.services.services:

            if service.state != "running":
                continue

            implementation = IMPLEMENTATIONS.get(
                service.name,
            )

            if implementation is None:
                continue

            implementations.append(
                CapabilityImplementation(
                    name=implementation,
                )
            )

        if not implementations:
            return None

        return Capability(
            kind=CapabilityKind.CONTAINER_RUNTIME,
            implementations=implementations,
        )
