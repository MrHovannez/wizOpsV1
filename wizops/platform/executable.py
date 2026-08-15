from __future__ import annotations

from wizops.inventory.models import ExecutableInventory


class ExecutableProvider:

    def snapshot(self) -> ExecutableInventory:
        return ExecutableInventory()
