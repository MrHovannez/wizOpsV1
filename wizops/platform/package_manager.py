from __future__ import annotations

from wizops.inventory.models import PackageManagerInventory


class PackageManagerProvider:

    def snapshot(self) -> PackageManagerInventory:
        return PackageManagerInventory()
