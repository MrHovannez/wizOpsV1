from wizops.platform.hardware import HardwareProvider
from wizops.platform.memory import MemoryProvider
from wizops.platform.network import NetworkProvider
from wizops.platform.storage import StorageProvider

from .cpu import LinuxCpuProvider
from .gpu.provider import LinuxGpuProvider
from .package_manager import LinuxPackageManagerProvider
from .identity import LinuxIdentityProvider
from .journal import LinuxJournalProvider
from .services import LinuxServiceProvider
from .executable import LinuxExecutableProvider


class LinuxPlatform:

    def __init__(self):

        self.identity = LinuxIdentityProvider()
        self.package_manager = LinuxPackageManagerProvider()
        self.cpu = LinuxCpuProvider()
        self.gpu = LinuxGpuProvider()
        self.memory = MemoryProvider()
        self.storage = StorageProvider()
        self.network = NetworkProvider()

        self.hardware = HardwareProvider(
            cpu=self.cpu,
            gpu=self.gpu,
            memory=self.memory,
            storage=self.storage,
        )

        self.services = LinuxServiceProvider()
        self.journal = LinuxJournalProvider()
        self.executable = LinuxExecutableProvider()
