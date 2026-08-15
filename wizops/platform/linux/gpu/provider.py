from __future__ import annotations

from wizops.inventory.models import Gpu

from .amd import AmdGpuProvider
from .intel import IntelGpuProvider
from .nvidia import NvidiaGpuProvider


class LinuxGpuProvider:

    def __init__(self):

        self.providers = [
            NvidiaGpuProvider(),
            AmdGpuProvider(),
            IntelGpuProvider(),
        ]

    def snapshot(self) -> list[Gpu]:

        for provider in self.providers:

            gpus = provider.snapshot()

            if gpus:
                return gpus

        return []
