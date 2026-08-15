from dataclasses import dataclass

from rich.text import Text


@dataclass(frozen=True)
class RenderedPanel:
    text: Text
    border_color: str
