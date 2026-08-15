from __future__ import annotations

import os
from pathlib import Path


# Root of the WizardOps source tree (development only).
SOURCE_ROOT = Path(__file__).resolve().parents[2]


# Root directory for WizardOps runtime data.
DATA_DIR = Path(
    os.environ.get(
        "WIZOPS_DATA_DIR",
        Path.home() / ".wizops",
    )
)


# SQLite event archive.
DB_PATH = Path(
    os.environ.get(
        "WIZOPS_DB_PATH",
        DATA_DIR / "events.db",
    )
)


# WizardOps log directory.
LOG_DIR = Path(
    os.environ.get(
        "WIZOPS_LOG_DIR",
        DATA_DIR / "logs",
    )
)


# Future directories.
ARCHIVE_DIR = Path(
    os.environ.get(
        "WIZOPS_ARCHIVE_DIR",
        DATA_DIR / "archive",
    )
)

EXPORT_DIR = Path(
    os.environ.get(
        "WIZOPS_EXPORT_DIR",
        DATA_DIR / "exports",
    )
)

CONFIG_DIR = Path(
    os.environ.get(
        "WIZOPS_CONFIG_DIR",
        DATA_DIR / "config",
    )
)
