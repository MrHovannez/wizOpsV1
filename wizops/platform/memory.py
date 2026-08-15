from __future__ import annotations

import psutil

from wizops.inventory.models import Memory


class MemoryProvider:

    def snapshot(self) -> Memory:

        memory = psutil.virtual_memory()

        return Memory(
            total=memory.total,
        )
