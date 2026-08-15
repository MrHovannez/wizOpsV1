from __future__ import annotations

import subprocess

from wizops.inventory.models import Service
from wizops.inventory.models import ServiceInventory


STATE_MAP = {
    "active": "running",
    "inactive": "stopped",
    "failed": "failed",
    "activating": "starting",
    "deactivating": "stopping",
}


class LinuxServiceProvider:

    def snapshot(self) -> ServiceInventory:

        result = subprocess.run(
            [
                "systemctl",
                "list-units",
                "--type=service",
                "--all",
                "--plain",
                "--no-legend",
                "--no-pager",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        enabled = self._enabled_services()

        services: list[Service] = []

        for line in result.stdout.splitlines():

            if not line.strip():
                continue

            parts = line.split(maxsplit=4)

            if len(parts) != 5:
                continue

            unit = parts[0]

            services.append(
                Service(
                    name=self._service_name(unit),
                    state=STATE_MAP.get(parts[2], "unknown"),
                    enabled=unit in enabled,
                )
            )

        return ServiceInventory(
            services=services,
        )

    def _enabled_services(self) -> set[str]:

        result = subprocess.run(
            [
                "systemctl",
                "list-unit-files",
                "--type=service",
                "--no-legend",
                "--no-pager",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        enabled = set()

        for line in result.stdout.splitlines():

            parts = line.split()

            if len(parts) < 2:
                continue

            if parts[1] == "enabled":
                enabled.add(parts[0])

        return enabled

    @staticmethod
    def _service_name(
        unit: str,
    ) -> str:

        if unit.endswith(".service"):
            return unit[:-8]

        return unit

    def discoverable(self) -> list[Service]:

        return [
            service
            for service in self.snapshot().services
            if service.state == "running"
        ]
