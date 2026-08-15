from __future__ import annotations

from wizops.collectors.file_logs import FileLogCollector
from wizops.domain import FileSource
from wizops.collectors.journal import JournalCollector
from wizops.domain import JournalSource


def build_file_job(store, source: FileSource):
    return (
        FileLogCollector(store),
        {
            "service": source.service,
            "path": source.path,
        },
    )


def build_journal_job(store, source: JournalSource):
    return (
        JournalCollector(store),
        {
            "service": source.service,
            "unit": source.unit,
        },
    )


FACTORIES = {
    FileSource: build_file_job,
    JournalSource: build_journal_job,
}
