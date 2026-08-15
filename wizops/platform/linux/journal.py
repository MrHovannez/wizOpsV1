import json
import subprocess

from .models import LinuxJournalEntry
from .models import JournalQuery

from wizops.orchestration.provider import CollectionProvider
from wizops.orchestration.models import CollectorRequest, CollectorPage


class LinuxJournalProvider(CollectionProvider):

    def search(self, query: JournalQuery):
        """
        Compatibility wrapper for the old API.

        Existing callers can continue using search() until they
        are migrated to CollectorRequest/CollectorPage.
        """

        page = self.fetch(
            CollectorRequest(
                limit=query.limit,
                unit=query.unit,
                since=query.since,
                until=query.until,
            )
        )
        return page.entries


    def fetch(
        self,
        request: CollectorRequest,
    ) -> CollectorPage:
        cmd = [
            "journalctl",
            "--no-pager",
            "-o",
            "json",
        ]
        if request.unit:
            cmd += ["-u", request.unit]
        if request.cursor:
            cmd += ["--after-cursor", request.cursor]
        if request.since:
            cmd += ["--since", self._translate_window(request.since)]
        if request.until:
            cmd += ["--until", request.until]
        if request.limit:
            cmd += ["-n", str(request.limit)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())
        entries = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            entries.append(
                LinuxJournalEntry(
                    timestamp=int(record.get("__REALTIME_TIMESTAMP", 0)),
                    hostname=record.get("_HOSTNAME", ""),
                    unit=record.get("_SYSTEMD_UNIT", ""),
                    identifier=record.get("SYSLOG_IDENTIFIER", ""),
                    priority=int(record.get("PRIORITY", 6)),
                    message=record.get("MESSAGE", ""),
                    cursor=record.get("__CURSOR", "")
                )
            )
        return CollectorPage(entries=entries)


    def _translate_window(self, window: str) -> str:
        if window.endswith("d"):
            return f"{window[:-1]} days ago"
        if window.endswith("h"):
            return f"{window[:-1]} hours ago"
        if window.endswith("m"):
            return f"{window[:-1]} minutes ago"
        return window


