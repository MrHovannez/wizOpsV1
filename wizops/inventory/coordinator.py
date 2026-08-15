from __future__ import annotations

from wizops.inventory.models import InventorySnapshot
from wizops.platform.linux.linux_platform import LinuxPlatform


class InventoryCoordinator:

    def __init__(
        self,
        platform: LinuxPlatform,
    ):
        self.platform = platform

    def snapshot(self) -> InventorySnapshot:

        return InventorySnapshot(
            package_managers=self.platform.package_manager.snapshot(),
            executables=self.platform.executable.snapshot(),
            identity=self.platform.identity.snapshot(),
            hardware=self.platform.hardware.snapshot(),
            network=self.platform.network.snapshot(),
            services=self.platform.services.snapshot(),
        )
