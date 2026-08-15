from rich.text import Text

from wizops.application.models import CollectionStatus
from wizops.presentation.renderers.panel import RenderedPanel
from wizops.presentation.formatting import clean_timestamp

def clean_timestamp(value):
    return (value or "").replace("Z", "")

class CollectionRenderer:

    @staticmethod
    def render(status: CollectionStatus) -> RenderedPanel:

        collect = Text()

        collect.append(
            "◉ COLLECTION & COVERAGE\n\n",
            style="bold #ff62ec",
        )

        collect.append(
            "Collectors active     ",
            style="#7395b2",
        )
        collect.append(
            f"{status.collectors_active:>5}\n",
            style="bold #55ff9a",
        )

        collect.append(
            "Last state update      ",
            style="#7395b2",
        )
        collect.append(
            f"{status.latest_state}\n",
            style="#62f5ff",
        )

        collect.append(
            "Coverage               ",
            style="#7395b2",
        )
        collect.append(
            f"{clean_timestamp(status.first_ts).replace('T',' ')[:10]} → "
            f"{clean_timestamp(status.last_ts).replace('T',' ')[:10]}\n",
            style="#d65cff",
        )

        collect.append(
            "Collector state        ",
            style="#7395b2",
        )
        collect.append(
            "ACTIVE",
            style="bold #55ff9a",
        )

        return RenderedPanel(
            text=collect,
            border_color="#ff62ec",
        )
