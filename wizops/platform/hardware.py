from __future__ import annotations

from wizops.inventory.models import HardwareInventory


class HardwareProvider:

    def __init__(
        self,
        cpu,
        gpu,
        memory,
        storage,
    ):
        self.cpu = cpu
        self.gpu = gpu
        self.memory = memory
        self.storage = storage

    def snapshot(self) -> HardwareInventory:

        return HardwareInventory(
            cpu=self.cpu.snapshot(),
            gpu=self.gpu.snapshot(),
            memory=self.memory.snapshot(),
            storage=self.storage.snapshot(),
        )
