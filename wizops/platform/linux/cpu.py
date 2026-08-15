from __future__ import annotations

import platform
from pathlib import Path

import psutil

from wizops.inventory.models import Cpu


class LinuxCpuProvider:

    def snapshot(self) -> Cpu:

        info = self._cpuinfo()

        return Cpu(
            vendor=info.get("vendor_id", "Unknown"),
            model=info.get("model name", "Unknown"),
            architecture=platform.machine(),
            physical_cores=psutil.cpu_count(logical=False) or 0,
            logical_cores=psutil.cpu_count(logical=True) or 0,
        )

    def _cpuinfo(self) -> dict[str, str]:

        result: dict[str, str] = {}

        try:
            for line in Path("/proc/cpuinfo").read_text().splitlines():

                if ":" not in line:
                    continue

                key, value = line.split(":", 1)

                key = key.strip()
                value = value.strip()

                if key not in result:
                    result[key] = value

        except OSError:
            pass

        return result
