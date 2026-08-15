from __future__ import annotations

from wizops.inventory.models import (
    Capability,
    CapabilityImplementation,
    CapabilityKind,
    InventorySnapshot,
)

from ..recognizer import CapabilityRecognizer


class GpuComputeRecognizer(CapabilityRecognizer):

    def recognize(
        self,
        inventory: InventorySnapshot,
    ) -> Capability | None:

        if inventory.hardware is None:
            return None

        if not inventory.hardware.gpu:
            return None

        implementations = []

        for gpu in inventory.hardware.gpu:
            implementations.append(
                CapabilityImplementation(
                    name=gpu.model,
                )
            )

        return Capability(
            kind=CapabilityKind.GPU_COMPUTE,
            implementations=implementations,
        )
