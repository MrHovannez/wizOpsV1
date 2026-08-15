from __future__ import annotations

from wizops.inventory.models import Gpu


class IntelGpuProvider:

    def snapshot(self) -> list[Gpu]:
        return []
