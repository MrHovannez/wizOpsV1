from __future__ import annotations

import os
from rich.text import Text

from wizops.application.models import SystemStatus
from wizops.presentation.formatting import human_size
from wizops.presentation.renderers.panel import RenderedPanel


class SystemRenderer:

    @staticmethod
    def _gauge(
        label: str,
        pct: float,
        value: str,
        color: str = "#55ff9a",
        width: int = 46,
    ) -> Text:

        pct = max(0.0, min(100.0, pct))
        fill = int(round(pct / 100 * width))

        t = Text()
        t.append(f"{label:<12}", style="#7395b2")
        t.append("█" * fill, style=color)
        t.append("░" * (width - fill), style="#10345d")
        t.append(
            f"  {pct:5.1f}%  {value}\n",
            style="#d8e7ff",
        )
        return t

    @staticmethod
    def render(status: SystemStatus) -> RenderedPanel:

        system = Text()

        system.append(
            "▣ SYSTEM AT A GLANCE\n\n",
            style="bold #00d9ff",
        )

        cpu_pct = min(
            100.0,
            (status.load1 / (os.cpu_count() or 1)) * 100,
        )

        system.append(
            SystemRenderer._gauge(
                "CPU LOAD",
                cpu_pct,
                f"load {status.load1:.2f}",
                "#00eaff",
            )
        )

        if status.mem_total and status.mem_avail:

            mem_used = status.mem_total - status.mem_avail
            mem_pct = mem_used / status.mem_total * 100

            system.append(
                SystemRenderer._gauge(
                    "MEMORY",
                    mem_pct,
                    f"{human_size(mem_used)} / {human_size(status.mem_total)}",
                    "#55ff9a" if mem_pct < 75 else "#ffb000",
                )
            )

        else:
            system.append(
                "MEMORY      unavailable\n",
                style="dim",
            )

        if (
            status.gpu_used is not None
            and status.gpu_total is not None
        ):

            pct = (
                status.gpu_used
                / status.gpu_total
                * 100
            )

            system.append(
                SystemRenderer._gauge(
                    "VRAM",
                    pct,
                    f"{status.gpu_used/1024:.1f} / {status.gpu_total/1024:.1f} GiB",
                    "#d65cff" if pct < 80 else "#ff416c",
                )
            )

        else:
            system.append(
                "VRAM        unavailable\n",
                style="dim",
            )

        disk_pct = (
            status.disk_used
            / status.disk_total
            * 100
            if status.disk_total
            else 0
        )

        system.append(
            SystemRenderer._gauge(
                "FILESYSTEM",
                disk_pct,
                f"{human_size(status.disk_used)} / {human_size(status.disk_total)}",
                "#55ff9a"
                if disk_pct < 75
                else "#ffb000"
                if disk_pct < 90
                else "#ff416c",
            )
        )

        system.append("\n")

        # Host/runtime summary.
        # Keep this to two rows so narrow dashboard panels
        # never clip the final field.

        system.append(
            f"HOST  {status.hostname}",
            style="#62f5ff",
        )

        system.append(
            f"    CONTAINERS  {status.container_count:>3} running\n",
            style="#00d9ff",
        )

        system.append(
            f"MODELS  {status.loaded_models:>3} loaded",
            style="#d65cff",
        )

        system.append(
            f"    COLLECTORS  {status.collectors_active:>3} active\n",
            style="#ffb000",
        )

        system.append(
            "LOCAL PROBES • live host resource gauges",
            style="#52799c",
        )

        return RenderedPanel(
            text=system,
            border_color="#00d9ff",
        )
