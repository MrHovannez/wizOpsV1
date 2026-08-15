from __future__ import annotations

from shutil import which

from wizops.inventory.models import (
    PackageManager,
    PackageManagerInventory,
)


PACKAGE_MANAGERS = (
    "dnf",
    "apt",
    "pacman",
    "zypper",
    "rpm",
    "dpkg",
    "apk",
    "emerge",
    "xbps-install",
    "brew",
)


class LinuxPackageManagerProvider:

    def snapshot(self) -> PackageManagerInventory:

        managers: list[PackageManager] = []

        for name in PACKAGE_MANAGERS:

            if which(name):

                managers.append(
                    PackageManager(
                        name=name,
                    )
                )

        return PackageManagerInventory(
            managers=managers,
        )
