from __future__ import annotations

import shutil

import psutil

from wizops.inventory.models import Storage


class StorageProvider:

    def snapshot(self) -> list[Storage]:

        storage = []

        for partition in psutil.disk_partitions(all=False):

            try:
                usage = shutil.disk_usage(partition.mountpoint)

                storage.append(
                    Storage(
                        device=partition.device,
                        mountpoint=partition.mountpoint,
                        filesystem_type=partition.fstype,
                        total=usage.total,
                        used=usage.used,
                        free=usage.free,
                        percent_used=usage.used / usage.total * 100,
                    )
                )

            except OSError:
                # Ignore inaccessible mounts.
                continue

        return storage
