from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from wizops.platform.linux.linux_platform import LinuxPlatform


@dataclass(frozen=True, slots=True)
class FileSource:
    service: str
    path: Path


@dataclass(frozen=True, slots=True)
class JournalSource:
    service: str
    unit: str



def discovered_sources():
    platform = LinuxPlatform()

    return [
        JournalSource(
            service=service.name,
            unit=f"{service.name}.service",
        )
        for service in platform.services.discoverable()
    ]


def iter_sources():
    yield from discovered_sources()
