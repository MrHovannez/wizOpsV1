from __future__ import annotations

import platform

import psutil

from wizops.inventory.models import Cpu


class CpuProvider:

    def snapshot(self) -> Cpu:

        return Cpu(
            vendor=platform.processor() or "Unknown",
            model=platform.processor() or "Unknown",
            architecture=platform.machine(),
            physical_cores=psutil.cpu_count(logical=False) or 0,
            logical_cores=psutil.cpu_count(logical=True) or 0,
        )
