from __future__ import annotations

from wizops.events.mapping.journal import journal_entry_to_event
from wizops.events.sources.base import EventSource
from wizops.platform.linux.models import JournalQuery


class JournalEventSource(EventSource):

    def __init__(self, provider):
        self.provider = provider

    def list_events(self):
        entries = self.provider.search(JournalQuery())

        return [
            journal_entry_to_event(entry)
            for entry in entries
        ]

    def search_events(self, where, params):
        raise NotImplementedError
