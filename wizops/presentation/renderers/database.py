from rich.text import Text

from wizops.application.models import DatabaseStatus
from wizops.presentation.renderers.panel import RenderedPanel

from wizops.presentation.formatting import (
    clean_timestamp,
    human_size,
)


class DatabaseRenderer:

    @staticmethod
    def render(status: DatabaseStatus) -> RenderedPanel:

        database = Text()

        database.append(
            "▦ EVENTS IN DATABASE\n\n",
            style="bold #d65cff",
        )

        database.append(
            "Lifetime events        ",
            style="#7395b2",
        )
        database.append(
            f"{status.lifetime_total:>10,}\n",
            style="bold #d65cff",
        )

        database.append(
            "Oldest event           ",
            style="#7395b2",
        )
        database.append(
            f"{clean_timestamp(status.first_ts).replace('T',' ')[:19]}\n",
            style="#62f5ff",
        )

        database.append(
            "Newest event           ",
            style="#7395b2",
        )
        database.append(
            f"{clean_timestamp(status.last_ts).replace('T',' ')[:19]}\n",
            style="#62f5ff",
        )

        database.append(
            "Database size          ",
            style="#7395b2",
        )
        database.append(
            f"{human_size(status.database_size):>10}",
            style="#55ff9a",
        )

        return RenderedPanel(
            text=database,
            border_color="#d65cff",
        )
