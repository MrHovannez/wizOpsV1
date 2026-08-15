from .models import SystemOverview
from wizops.platform.linux.linux_platform import LinuxPlatform


class SystemService:

    def __init__(self, platform: LinuxPlatform):
        self.platform = platform

    def overview(self) -> SystemOverview:
        return SystemOverview(
            cpu=self.platform.cpu.snapshot(),
            memory=self.platform.memory.snapshot(),
            storage=self.platform.storage.snapshot("/"),
            network=self.platform.network.snapshot(),
        )
