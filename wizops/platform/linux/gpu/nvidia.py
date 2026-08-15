from __future__ import annotations

import subprocess

from wizops.inventory.models import Gpu


class NvidiaGpuProvider:

    def snapshot(self) -> list[Gpu]:

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

        except (
            FileNotFoundError,
            subprocess.CalledProcessError,
        ):
            return []

        gpus: list[Gpu] = []

        for line in result.stdout.splitlines():

            if not line.strip():
                continue

            parts = [part.strip() for part in line.split(",", 1)]

            if len(parts) != 2:
                continue

            model = parts[0]

            try:
                memory = int(parts[1]) * 1024 * 1024
            except ValueError:
                memory = None

            gpus.append(
                Gpu(
                    vendor="NVIDIA",
                    model=model,
                    memory_total=memory,
                )
            )

        return gpus
