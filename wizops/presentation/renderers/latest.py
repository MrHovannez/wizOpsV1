from __future__ import annotations

from rich.text import Text

from wizops.application.models import LatestStatus
from wizops.presentation.formatting import (
    COLORS,
    clean,
    local_timestamp,
    summary,
)
from wizops.presentation.renderers.panel import RenderedPanel


class LatestRenderer:

    @staticmethod
    def render(status: LatestStatus) -> RenderedPanel:

        latest = status.event

        card = Text()

        card.append(
            "⚠ LATEST ATTENTION EVENT\n\n",
            style="bold #ff62ec",
        )

        if latest:

            card.append(
                f"{local_timestamp(clean(latest['timestamp']), '%H:%M:%S')}   "
            )

            card.append(
                f"{latest['severity']:<5}",
                style=COLORS.get(
                    latest["severity"],
                    "#d8e7ff",
                ),
            )

            card.append(
                f"   {latest['service']}\n",
                style="#62f5ff",
            )

            card.append(
                summary(
                    latest["message"],
                    92,
                )
                + "\n\n",
                style="#d8e7ff",
            )

            card.append(
                "  [ ENTER ]  VIEW EVENT  ",
                style="bold #020712 on #ff62ec",
            )

        else:

            card.append(
                "No attention events",
                style="dim",
            )

        return RenderedPanel(
            text=card,
            border_color="#ff62ec",
        )
