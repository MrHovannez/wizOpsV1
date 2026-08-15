from dataclasses import dataclass


@dataclass(frozen=True)
class InvestigationResult:
    related_events: list
    pattern_summary: tuple


class InvestigationService:
    def __init__(self, store):
        self.store = store

    def inspect(self, row):
        related = self.store.related_events(
            event_id=row["id"],
            service=row["service"],
            category=row["category"],
            request_id=row["request_id"],
            model=row["model"],
        )

        pattern = self.store.pattern_summary(
            row["service"],
            row["message"],
        )

        return InvestigationResult(
            related_events=related,
            pattern_summary=pattern,
        )
