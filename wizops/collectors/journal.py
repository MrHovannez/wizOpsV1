from __future__ import annotations

from wizops.events.archive import ArchiveStore
from wizops.events.mapping.journal import journal_entry_to_event
from wizops.platform.linux.journal import LinuxJournalProvider
from wizops.orchestration.models import CollectorRequest
from wizops.orchestration.policy import CollectionPolicy


class JournalCollector:

    collector_id = "journal-v1"

    def __init__(self, store: ArchiveStore):
        self.store = store
        self.provider = LinuxJournalProvider()

    def collect(self, *, unit: str, service: str):

        policy = CollectionPolicy()
        source = f"journal:{unit}"

        state = self.store.collector_state.get_state(
            self.collector_id,
            source,
        )

        cursor = state["cursor"] if state else None

        request = CollectorRequest(
            unit=unit,
            cursor=cursor,
            since=None if cursor else policy.recent_window,
            limit=policy.page_size,
        )

        page = self.provider.fetch(request)

        last_cursor = cursor
        last_timestamp = state["last_timestamp"] if state else None

        for entry in page.entries:

            event = journal_entry_to_event(entry)

            last_cursor = entry.cursor
            last_timestamp = event.timestamp

            yield event

        self.store.collector_state.set_state(
            self.collector_id,
            source,
            0,
            0,
            last_timestamp,
            cursor=last_cursor,
        )
