from __future__ import annotations

from wizops.inventory.models import Gpu


class AmdGpuProvider:

    def snapshot(self) -> list[Gpu]:
        return []
