from wizops.events.event import Event
from wizops.platform.linux.models import LinuxJournalEntry


class JournalEventMapper:

    def to_event(self, entry: LinuxJournalEntry) -> Event:
        raise NotImplementedError
