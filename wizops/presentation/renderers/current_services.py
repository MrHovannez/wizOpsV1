from __future__ import annotations

from collections import defaultdict

from rich.text import Text


class CurrentServicesRenderer:

    MAX_VISIBLE = 20

    # Width available to each service column.
    # This is deliberately conservative so long systemd names
    # cannot collide with the other column.

    # Space separating the two columns.
    COLUMN_GAP = 3

    @staticmethod
    def _service_family(name: str) -> str | None:
        """
        Return a grouping key for related services.

        Examples:

            abrt-journal-core -> abrt
            abrt-oops         -> abrt
            abrt-xorg         -> abrt
        """

        if "-" not in name:
            return None

        prefix = name.split("-", 1)[0]

        if len(prefix) >= 3:
            return prefix

        return None

    @staticmethod
    def _truncate(name: str, width: int) -> str:
        """
        Keep a service name inside its column.
        """

        if len(name) <= width:
            return name

        if width <= 3:
            return name[:width]

        return name[: width - 3] + "..."

    @staticmethod
    @staticmethod
    def _build_blocks(
        services,
        column_width: int,
    ) -> list[list[Text]]:
        """
        Build complete visual blocks.

        A grouped service family is one block, so it can never
        be split between the two columns.
        """

        families: dict[str, list] = defaultdict(list)
        standalone = []

        for service in services:

            family = CurrentServicesRenderer._service_family(
                service.name
            )

            if family:
                families[family].append(service)
            else:
                standalone.append(service)

        grouped = []

        for family, members in families.items():

            if len(members) >= 2:
                grouped.append((family, members))
            else:
                standalone.extend(members)

        grouped.sort(
            key=lambda item: item[0].lower()
        )

        standalone.sort(
            key=lambda service: service.name.lower()
        )

        blocks: list[list[Text]] = []

        # ---------------------------------------------
        # Grouped families
        # ---------------------------------------------

        for family, members in grouped:

            block: list[Text] = []

            header = Text()

            header.append(
                "● ",
                style="#38f2ff",
            )

            header.append(
                f"{family.upper()} ",
                style="bold #ffb000",
            )

            header.append(
                f"({len(members)})",
                style="#62f5ff",
            )

            block.append(header)

            for index, member in enumerate(members):

                line = Text()

                connector = (
                    "  └ "
                    if index == len(members) - 1
                    else "  ├ "
                )

                line.append(
                    connector,
                    style="#7c3cff",
                )

                available = (
                    column_width
                    - len(connector)
                )

                line.append(
                    CurrentServicesRenderer._truncate(
                        member.name,
                        available,
                    ),
                    style="#d8e7ff",
                )

                block.append(line)

            blocks.append(block)

        # ---------------------------------------------
        # Standalone services
        # ---------------------------------------------

        for service in standalone:

            line = Text()

            line.append(
                "● ",
                style="#38f2ff",
            )

            line.append(
                CurrentServicesRenderer._truncate(
                    service.name,
                    column_width - 2,
                ),
                style="#d8e7ff",
            )

            blocks.append([line])

        return blocks

    @staticmethod
    def _column_height(blocks: list[list[Text]]) -> int:
        """
        Return the visual height of a column.
        """

        return sum(len(block) for block in blocks)

    @staticmethod
    def _split_columns(
        blocks: list[list[Text]],
    ) -> tuple[list[list[Text]], list[list[Text]]]:
        """
        Distribute complete blocks between two columns.

        We use a greedy height-balancing approach rather than
        simply splitting the list in half.
        """

        left: list[list[Text]] = []
        right: list[list[Text]] = []

        left_height = 0
        right_height = 0

        for block in blocks:

            block_height = len(block)

            if left_height <= right_height:
                left.append(block)
                left_height += block_height
            else:
                right.append(block)
                right_height += block_height

        return left, right

    @staticmethod
    def render(services, width: int = 80) -> Text:

        width = max(40, width)

        column_width = max(
            18,
            (width - CurrentServicesRenderer.COLUMN_GAP) // 2,
        )

        all_running = [
            service
            for service in services
            if service.state == "running"
        ]

        running = all_running[
            : CurrentServicesRenderer.MAX_VISIBLE
        ]

        text = Text()

        text.append(
            "● RUNNING SERVICES  ",
            style="bold #00d9ff",
        )

        text.append(
            f"{len(running)} SHOWN / {len(all_running)} RUNNING\n\n",
            style="bold #62f5ff",
        )

        if not running:

            text.append(
                "No running services detected.",
                style="#d8e7ff",
            )

            return text

        blocks = CurrentServicesRenderer._build_blocks(
            running,
            column_width,
        )

        left, right = CurrentServicesRenderer._split_columns(
            blocks
        )

        left_height = CurrentServicesRenderer._column_height(
            left
        )

        right_height = CurrentServicesRenderer._column_height(
            right
        )

        row_count = max(
            left_height,
            right_height,
        )

        # Flatten each column while preserving block boundaries.
        left_lines = [
            line
            for block in left
            for line in block
        ]

        right_lines = [
            line
            for block in right
            for line in block
        ]

        # ---------------------------------------------
        # Render independent columns
        # ---------------------------------------------

        for index in range(row_count):

            if index < len(left_lines):

                left_line = left_lines[index]

                text.append(left_line)

                # Pad according to the actual rendered length.
                # This keeps the second column fixed in place.
                remaining = (
                    column_width
                    - left_line.cell_len
                )

                if remaining > 0:
                    text.append(" " * remaining)

            else:

                text.append(
                    " " * column_width
                )

            text.append(
                " " * CurrentServicesRenderer.COLUMN_GAP
            )

            if index < len(right_lines):
                text.append(right_lines[index])

            text.append("\n")

        return text
