from __future__ import annotations

from datetime import datetime
from pathlib import Path

from wizops.config import EXPORT_DIR

from wizops.infrastructure.clipboard import Clipboard

from wizops.presentation.formatting import (
    clean,
    local_timestamp,
    pretty_raw,
)

from .models import ExportResult


SEPARATOR = "=" * 40

class ExportService:
    def __init__(self):
        self.export_dir = EXPORT_DIR
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.clipboard = Clipboard()

    def event_text(self, row):
        if not row:
            return ""
        fields = [
            SEPARATOR,
            f"EVENT #{row['id']}",
            f"TIME: {local_timestamp(clean(row['timestamp']))}",
            f"SEVERITY: {clean(row['severity'])}",
            f"SERVICE: {clean(row['service'])}",
            f"SOURCE: {clean(row['source_type'])} · {clean(row['source'])}",
        ]
        if row["category"]:
            fields.append(f"CATEGORY: {clean(row['category'])}")
        if row["model"]:
            fields.append(f"MODEL: {clean(row['model'])}")
        if row["request_id"]:
            fields.append(f"REQUEST: {clean(row['request_id'])}")
        fields += [
            "",
            "MESSAGE",
            clean(row["message"]),
            "",
            "RAW EVENT",
            pretty_raw(row["raw_event"]),
        ]
        return "\n".join(fields).rstrip()


    def clipboard_text(self, rows) -> str:
        rows = list(rows)
        return "\n\n".join(
            self.event_text(row)
            for row in rows
        )

    def export(
        self,
        rows,
        label,
        *,
        service=None,
        severity=None,
        time_range="ALL",
        search=None,
    ) -> ExportResult:

        rows = list(rows)

        if not rows:
            return ExportResult(
                success=False,
                message="No events to export.",
                path=None,
            )

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        path = self.export_dir / f"{label}-{stamp}.txt"

        header = [
            "WIZARD HOV CONSOLE EVENT EXPORT",
            f"scope: {label}",
            f"events: {len(rows)}",
            f"service filter: {service or 'ALL'}",
            f"severity filter: {severity or 'ALL'}",
            f"time range: {time_range}",
            f"search: {search or '—'}",
            "",
        ]

        body = ("\n" + "=" * 100 + "\n\n").join(
            self.event_text(row)
            for row in rows
        )

        path.write_text("\n".join(header) + body)

        return ExportResult(
            success=True,
            message=f"Exported {len(rows):,} event(s) • {path}",
            path=path,
        )

    def copy(self, text: str):
        return self.clipboard.copy(text)
