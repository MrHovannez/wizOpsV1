from __future__ import annotations

from wizops.inventory.models import Gpu


class GpuProvider:

    def snapshot(self) -> list[Gpu]:
        """
        Return the GPUs installed in the system.

        The shared provider intentionally returns an empty list.
        Platforms that can discover GPUs should provide their own
        implementation.
        """
        return []
