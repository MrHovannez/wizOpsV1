from __future__ import annotations

from rich.text import Text

from wizops.application.models import ServicesStatus
from wizops.presentation.renderers.panel import RenderedPanel


class ServicesRenderer:

    COLUMN_GAP = 6
    MAX_SERVICES = 10

    @staticmethod
    def _truncate(name: str, width: int) -> str:
        if width <= 0:
            return ""

        if len(name) <= width:
            return name

        if width <= 3:
            return name[:width]

        return name[: width - 3] + "..."

    @staticmethod
    def _render_entry(
        rank: int,
        name: str,
        count: int,
        peak: int,
        column_width: int,
    ) -> Text:

        text = Text(
            no_wrap=True,
            overflow="crop",
        )

        rank_width = 3
        count_width = 7
        gap_width = 1

        label_width = min(
            24,
            max(
                16,
                column_width // 3,
            ),
        )

        bar_width = max(
            4,
            column_width
            - rank_width
            - label_width
            - count_width
            - gap_width,
        )

        text.append(
            f"{rank:02d} ",
            style="bold #62f5ff",
        )

        text.append(
            ServicesRenderer._truncate(
                name,
                label_width,
            ).ljust(label_width),
            style="#d8e7ff",
        )

        if peak:
            filled = max(
                1,
                int(count / peak * bar_width),
            )
        else:
            filled = 0

        text.append(
            "█" * filled,
            style="#ffb000" if rank <= 3 else "#b87900",
        )

        text.append(
            "░" * (bar_width - filled),
            style="#26313a",
        )

        text.append(
            " ",
        )

        text.append(
            f"{count:>{count_width - 1},}",
            style="#62f5ff",
        )

        # Guarantee the entry occupies exactly column_width cells.
        current_width = text.cell_len

        if current_width < column_width:
            text.append(
                " " * (column_width - current_width)
            )

        return text



    @staticmethod
    def render(
        status: ServicesStatus,
        width: int = 80,
    ) -> RenderedPanel:

        services = list(
            status.services[: ServicesRenderer.MAX_SERVICES]
        )

        width = max(40, width)

        text = Text()

        text.append(
            "▸ TOP SERVICES  ",
            style="bold #ffb000",
        )

        text.append(
            "•  LAST 24H\n\n",
            style="bold #ffd35c",
        )

        if not services:
            text.append(
                "No events in last 24h.",
                style="#d8e7ff",
            )

            return RenderedPanel(
                text=text,
                border_color="#ffb000",
            )

        # Available width is divided between two columns.

        # The two columns and their gap must fit inside the
        # actual render width. Leave a small safety margin so
        # Rich never folds the next row onto the current one.
        usable_width = max(
            48,
            width - 4,
        )

        column_width = (
            usable_width
            - ServicesRenderer.COLUMN_GAP
        ) // 2

        peak = max(
            (count for _, count in services),
            default=1,
        )

        midpoint = (
            len(services) + 1
        ) // 2

        left = services[:midpoint]
        right = services[midpoint:]

        rows = max(
            len(left),
            len(right),
        )

        total_row_width = (
            column_width
            + ServicesRenderer.COLUMN_GAP
            + column_width
        )

        for index in range(rows):

            row = Text(
                no_wrap=True,
                overflow="crop",
            )

            # -------------------------------------------------
            # LEFT COLUMN
            # -------------------------------------------------

            if index < len(left):

                rank = index + 1
                name, count = left[index]

                row.append(
                    ServicesRenderer._render_entry(
                        rank,
                        name,
                        count,
                        peak,
                        column_width,
                    )
                )

            else:

                row.append(
                    " " * column_width
                )

            # -------------------------------------------------
            # COLUMN GAP
            # -------------------------------------------------

            row.append(
                " " * ServicesRenderer.COLUMN_GAP
            )

            # -------------------------------------------------
            # RIGHT COLUMN
            # -------------------------------------------------

            if index < len(right):

                rank = midpoint + index + 1
                name, count = right[index]

                row.append(
                    ServicesRenderer._render_entry(
                        rank,
                        name,
                        count,
                        peak,
                        column_width,
                    )
                )

            else:

                row.append(
                    " " * column_width
                )

            # -------------------------------------------------
            # HARD GUARANTEE
            # -------------------------------------------------

            if row.cell_len < total_row_width:
                row.append(
                    " " * (
                        total_row_width - row.cell_len
                    )
                )

            elif row.cell_len > total_row_width:
                row.truncate(
                    total_row_width,
                    overflow="crop",
                )

            text.append(row)
            text.append("\n")


        # -------------------------------------------------
        # SERVICE DISTRIBUTION
        # -------------------------------------------------

        top10_total = sum(
            count for _, count in services
        )

        other_events = max(
            status.total24 - top10_total,
            0,
        )

        other_services = max(
            status.distinct_services - len(services),
            0,
        )

        top10_share = (
            top10_total / status.total24 * 100
            if status.total24
            else 0
        )

        other_share = (
            other_events / status.total24 * 100
            if status.total24
            else 0
        )


        # -------------------------------------------------
        # SERVICE DISTRIBUTION / SUMMARY
        # -------------------------------------------------

        text.append("\n")

        text.append(
            "─" * max(40, width),
            style="#704f00",
        )

        text.append("\n")

        text.append(
            f"TOP 10       {top10_total:>8,} EVENTS"
            f"   {top10_share:>5.1f}%",
            style="bold #62f5ff",
        )

        text.append("\n")

        text.append(
            f"OTHER        {other_services:>8} SERVICES"
            f"   {other_events:>8,} EVENTS"
            f"   {other_share:>5.1f}%",
            style="#d8e7ff",
        )

        text.append("\n")

        text.append(
            f"TOTAL        {status.total24:>8,} EVENTS"
            f"   │   {status.distinct_services} DISTINCT SERVICES",
            style="bold #ffb000",
        )

        return RenderedPanel(
            text=text,
            border_color="#ffb000",
        )
