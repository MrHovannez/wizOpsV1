from .refresh import refresh
from .situation import SituationService
from .models import EventQuery, EventsResult
from .export import ExportService

from wizops.events.sources.sqlite import SQLiteEventSource
from wizops.events.sources.journal import JournalEventSource
from wizops.events.sources.composite import CompositeEventSource

class WizardingOpsApplication:

    def __init__(self, platform, store, db_path):
        self.platform = platform
        self.store = store
        self.db_path = db_path
        self.exporter = ExportService()

        archive = SQLiteEventSource(store)
        journal = JournalEventSource(platform.journal)

        self.event_source = CompositeEventSource(
            archive,
            journal,
        )

        self.situation = SituationService(
            self.platform,
            self.store,
            self.db_path,
        )

    def overview(self):
        return self.situation

    def events(self, query: EventQuery) -> EventsResult:
        def time_clause():
            return {
                "1H": "timestamp >= datetime('now','-1 hour')",
                "6H": "timestamp >= datetime('now','-6 hours')",
                "12H": "timestamp >= datetime('now','-12 hours')",
                "24H": "timestamp >= datetime('now','-24 hours')",
                "7D": "timestamp >= datetime('now','-7 days')",
                "30D": "timestamp >= datetime('now','-30 days')",
                "ALL": None,
            }.get(query.time_window)
        if query.severity == "ATTENTION":
            clauses = ["severity IN ('WARN','ERROR','FATAL')"]
            params = []
            if time_clause():
                clauses.append(time_clause())
            if query.service:
                clauses.append("service=?")
                params.append(query.service)
            if query.search:
                clauses.append(
                    "(message LIKE ? OR raw_event LIKE ? OR category LIKE ? OR model LIKE ? OR request_id LIKE ?)"
                )
                params += [f"%{query.search}%"] * 5
            rows = self.event_source.search_events(
                " WHERE " + " AND ".join(clauses),
                params,
            )
            return EventsResult(events=rows)
        clauses = []
        params = []
        if query.service:
            clauses.append("service=?")
            params.append(query.service)
        if query.severity:
            clauses.append("severity=?")
            params.append(query.severity)
        if time_clause():
            clauses.append(time_clause())
        if query.search:
            clauses.append(
                "(message LIKE ? OR raw_event LIKE ? OR category LIKE ? OR model LIKE ? OR request_id LIKE ?)"
            )
            params += [f"%{query.search}%"] * 5
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        rows = self.event_source.search_events(where, params)
        return EventsResult(events=rows)

    def inspect(self, event_id):
        raise NotImplementedError

    def refresh(self):
        raise NotImplementedError

    def export(
        self,
        rows,
        label,
        *,
        service=None,
        severity=None,
        time_range="ALL",
        search=None,
    ):
        return self.exporter.export(
            rows,
            label,
            service=service,
            severity=severity,
            time_range=time_range,
            search=search,
        )


    def copy(self, text: str):
        return self.exporter.copy(text)

    def clipboard_text(self, rows):
        return self.exporter.clipboard_text(rows)


    def services(self) -> list[str]:
        return self.store.distinct_services()
