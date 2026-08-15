from __future__ import annotations

import argparse
import os
import shutil as shell_tools
import subprocess
from pathlib import Path

from wizops.application import refresh
from wizops.config import DB_PATH
from wizops.events.archive import ArchiveStore
from wizops.startup import StartupScreen


def parser():
    p = argparse.ArgumentParser(
        prog="wizops",
        description="Wizarding Operations Console — system observability and event forensics.",
    )

    p.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help="Path to the WizOps event database.",
    )

    sub = p.add_subparsers(
        dest="command",
        required=True,
    )

    sub.add_parser(
        "init",
        help="Initialize the event database.",
    )

    sub.add_parser(
        "discover",
        help="Discover system services and collect recent events.",
    )

    sub.add_parser(
        "tui",
        help="Open the interactive WizOps console.",
    )

    sub.add_parser(
        "manual",
        help="Open the WizOps operator manual.",
    )

    return p


def main(argv=None):
    args = parser().parse_args(argv)

    store = ArchiveStore(args.db)

    try:
        store.init_schema()

        if args.command == "init":
            print(f"Initialized {args.db}")

        elif args.command == "discover":
            result = refresh(store)

            print("Collection complete!")
            print(f"Seen: {result.seen}")
            print(f"Inserted: {result.inserted}")
            print(f"Deduplicated: {result.deduplicated}")
            print(f"Elapsed time: {result.elapsed_time:.2f}s")

            if result.errors:
                print(f"Errors: {len(result.errors)}")

                for error in result.errors:
                    print(f"  - {error}")

        elif args.command == "manual":
            manual_path = (
                Path(__file__).resolve().parent.parent
                / "docs"
                / "manual.md"
            )

            if not manual_path.is_file():
                raise SystemExit(
                    f"WizOps manual not found: {manual_path}"
                )

            store.close()
            store = None

            pager = os.environ.get("PAGER")

            if pager:
                subprocess.run(
                    [pager, str(manual_path)],
                    check=False,
                )

            elif shell_tools.which("less"):
                subprocess.run(
                    ["less", "-R", str(manual_path)],
                    check=False,
                )

            else:
                print(
                    manual_path.read_text()
                )

        elif args.command == "tui":
            startup = StartupScreen()

            startup.add("Loading configuration")
            startup.add("Opening event database")
            startup.add("Synchronizing telemetry")
            startup.add("Preparing interface")

            for index in range(4):
                startup.start(index)
                startup.done()

            store.close()
            store = None

            try:
                from wizops.tui import run
            except ModuleNotFoundError as exc:
                if exc.name == "textual":
                    raise SystemExit(
                        "Textual is not installed."
                    )
                raise

            run(args.db)

    finally:
        if store is not None:
            store.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
