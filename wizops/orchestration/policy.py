from dataclasses import dataclass


@dataclass(slots=True)
class CollectionPolicy:
    recent_window: str = "5d"
    page_size: int = 250
