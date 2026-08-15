from __future__ import annotations

import platform
import socket
from pathlib import Path

from wizops.inventory.models import IdentityInventory


class LinuxIdentityProvider:

    def snapshot(self) -> IdentityInventory:

        return IdentityInventory(
            hostname=socket.gethostname(),
            operating_system="Linux",
            distribution=self._distribution(),
            kernel=platform.release(),
            architecture=platform.machine(),
        )

    def _distribution(self) -> str:

        os_release = Path("/etc/os-release")

        if not os_release.exists():
            return "Unknown Linux"

        values: dict[str, str] = {}

        for line in os_release.read_text().splitlines():

            line = line.strip()

            if not line or "=" not in line:
                continue

            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"')

        name = values.get("NAME")
        version = values.get("VERSION_ID")

        if name and version:
            return f"{name} {version}"

        return (
            values.get("PRETTY_NAME")
            or values.get("NAME")
            or "Unknown Linux"
        )
