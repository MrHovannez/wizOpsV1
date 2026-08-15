from pathlib import Path

from rich.text import Text

from wizops.application.situation import CapacityStatus
from wizops.presentation.renderers.panel import RenderedPanel


def _human(n: int) -> str:
    x = float(n)
    for u in ("B", "KiB", "MiB", "GiB", "TiB"):
        if x < 1024 or u == "TiB":
            return f"{x:,.1f} {u}"
        x /= 1024


class CapacityRenderer:
    """Renders the Observatory Capacity panel."""

    @staticmethod
    def render(status: CapacityStatus) -> RenderedPanel:
        text = Text()


        disk = status.storage

        log_size = status.log_size
        db_size = status.database_size

        pct = disk.percent_used
        used = disk.used
        free = disk.free
        total = disk.total

        bars = 24
        usedbars = min(bars, int(round(pct / 100 * bars)))

        gradient = [
            "#45ff9a",
            "#55ff7a",
            "#7dff55",
            "#b8ff3d",
            "#e8f52f",
            "#ffd21f",
            "#ffad16",
            "#ff7a20",
            "#ff4d38",
            "#ff315f",
        ]

        text.append("▣ STORAGE & CAPACITY\n\n", style="bold #55ff9a")

        text.append(
            f"Event logs                    {_human(log_size):>10}\n"
        )
        text.append(
            f"Console database            {_human(db_size):>10}\n\n"
        )

        text.append("Filesystem usage   ", style="bold #62f5ff")

        for i in range(usedbars):
            ratio = i / max(1, bars - 1)
            gi = min(len(gradient) - 1, int(ratio * (len(gradient) - 1)))
            text.append("█", style=gradient[gi])

        text.append("░" * (bars - usedbars), style="#10345d")

        pct_style = (
            "#55ff9a"
            if pct < 60
            else (
                "#e8f52f"
                if pct < 75
                else (
                    "#ffad16"
                    if pct < 90
                    else "#ff315f"
                )
            )
        )

        text.append(
            f"  {pct:5.1f}%\n",
            style=f"bold {pct_style}",
        )

        text.append(
            f"Used  {_human(used):>10}   "
            f"Free  {_human(free):>10}   "
            f"Total  {_human(total):>10}"
        )

        return RenderedPanel(
            text=text,
            border_color=pct_style,
        )
