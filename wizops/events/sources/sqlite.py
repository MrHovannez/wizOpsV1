from .base import EventSource
from wizops.events.archive import ArchiveStore


class SQLiteEventSource(EventSource):
    def __init__(self, archive):
        self.archive = archive

    def search_events(self, where, params):
        return self.archive.search_events(where, params)

    def list_events(self):
        return self.archive.list_events()
