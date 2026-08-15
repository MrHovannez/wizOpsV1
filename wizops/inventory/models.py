from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum



@dataclass(slots=True)
class InventorySnapshot:
    identity: "IdentityInventory | None" = None
    hardware: "HardwareInventory | None" = None
    services: "ServiceInventory | None" = None
    network: "NetworkInventory | None" = None
    package_managers: "PackageManagerInventory | None" = None
    executables: "ExecutableInventory | None" = None


@dataclass(slots=True)
class IdentityInventory:
    hostname: str
    operating_system: str
    distribution: str
    kernel: str
    architecture: str


@dataclass(slots=True)
class HardwareInventory:
    cpu: "Cpu | None" = None
    memory: "Memory | None" = None
    gpu: list["Gpu"] = field(default_factory=list)
    storage: list["Storage"] = field(default_factory=list)


@dataclass(slots=True)
class Cpu:
    vendor: str
    model: str
    architecture: str
    physical_cores: int
    logical_cores: int


@dataclass(slots=True)
class Memory:
    total: int


@dataclass(slots=True)
class Gpu:
    vendor: str
    model: str
    memory_total: int | None = None


@dataclass(slots=True)
class Storage:
    device: str
    mountpoint: str
    filesystem_type: str
    total: int
    used: int
    free: int
    percent_used: float


@dataclass(slots=True)
class ServiceInventory:
    services: list[Service] = field(default_factory=list)


@dataclass(slots=True)
class Service:
    name: str
    state: str
    enabled: bool | None = None


@dataclass(slots=True)
class NetworkInventory:
    interfaces: list["NetworkInterface"] = field(default_factory=list)


@dataclass(slots=True)
class NetworkInterface:
    name: str
    kind: str
    state: str
    mac_address: str | None
    ipv4: list[str] = field(default_factory=list)
    ipv6: list[str] = field(default_factory=list)



class CapabilityKind(str, Enum):
    CONTAINER_RUNTIME = "container_runtime"
    LLM_RUNTIME = "llm_runtime"
    RELATIONAL_DATABASE = "relational_database"
    VECTOR_DATABASE = "vector_database"
    GPU_COMPUTE = "gpu_compute"
    REMOTE_ACCESS = "remote_access"
    PACKAGE_MANAGER = "package_manager"
    SCHEDULER = "scheduler"


@dataclass(slots=True)
class CapabilityImplementation:
    name: str


@dataclass(slots=True)
class Capability:
    kind: CapabilityKind
    implementations: list[CapabilityImplementation] = field(
        default_factory=list
    )


@dataclass(slots=True)
class CapabilityInventory:
    capabilities: list[Capability] = field(default_factory=list)

    def has(
        self,
        kind: CapabilityKind,
    ) -> bool:

        return any(
            capability.kind == kind
            for capability in self.capabilities
        )

    def get(
        self,
        kind: CapabilityKind,
    ) -> Capability | None:

        for capability in self.capabilities:
            if capability.kind == kind:
                return capability

        return None

    def implementations(
        self,
        kind: CapabilityKind,
    ) -> list[CapabilityImplementation]:

        capability = self.get(kind)

        if capability is None:
            return []

        return capability.implementations



@dataclass(slots=True)
class PackageManager:
    name: str


@dataclass(slots=True)
class PackageManagerInventory:
    managers: list[PackageManager] = field(default_factory=list)


@dataclass(slots=True)
class Executable:
    name: str
    path: str


@dataclass(slots=True)
class ExecutableInventory:
    executables: list[Executable] = field(default_factory=list)


