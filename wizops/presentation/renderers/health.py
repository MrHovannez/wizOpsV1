from rich.text import Text

from wizops.application.models import HealthStatus
from wizops.presentation.renderers.panel import RenderedPanel


def _clean(ts: str | None) -> str:
    if not ts:
        return "-"
    return ts.replace("T", " ")[:19]


class HealthRenderer:
    """Renders the Observatory Health panel."""

    @staticmethod
    def render(status: HealthStatus) -> RenderedPanel:
        health = Text()

        health.append(
            "⌁ EVENT HEALTH  •  LAST 24H\n\n",
            style="bold #ff2f92",
        )

        health_width = 54

        for label, value, color in (
            ("ERROR", status.err24, "#ff416c"),
            ("WARN", status.warn24, "#ffb000"),
            ("FATAL", status.fatal24, "#ff62ec"),
            ("INFO", status.info24, "#00d9ff"),
        ):
            vals = status.sev_series[label]

            peak = max(vals) or 1

            spark_chars = "▁▂▃▄▅▆▇█"

            samples = []

            for x in range(health_width):
                lo = int(x * len(vals) / health_width)
                hi = max(lo + 1, int((x + 1) * len(vals) / health_width))
                samples.append(sum(vals[lo:hi]))

            health.append(
                f"{label:<6}",
                style=f"bold {color}",
            )

            health.append(
                f"{value:>8,}  ",
                style=f"bold {color}",
            )

            for v in samples:
                health.append(
                    spark_chars[min(7, int(v / peak * 7))] if v else "─",
                    style=color if v else "#17304a",
                )

            health.append(
                f"  peak {peak:,}/h\n",
                style=color,
            )

        attention_pct = (
            (status.attention24 / status.total24 * 100)
            if status.total24
            else 0
        )

        health.append("\n")

        health.append(
            f"TOTAL 24H  {status.total24:,}",
            style="bold #ff8dbd",
        )

        health.append(
            f"   │   ATTENTION  {status.attention24:,} ({attention_pct:.1f}%)",
            style="bold #ff62ec",
        )

        health.append(
            f"\nLIFETIME  {status.lifetime_total:,}"
            f"   │   FIRST  {_clean(status.first_ts)}"
            f"   │   LAST  {_clean(status.last_ts)}",
            style="#7395b2",
        )

        return RenderedPanel(
            text=health,
            border_color="#ff2f92",
        )
