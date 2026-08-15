from __future__ import annotations

import itertools
import sys
import threading
import time

SPINNER = itertools.cycle("⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏")


class StartupScreen:
    LOGO = r"""
██╗    ██╗██╗███████╗ ██████╗ ██████╗ ███████╗
██║    ██║██║╚══███╔╝██╔═══██╗██╔══██╗██╔════╝
██║ █╗ ██║██║  ███╔╝ ██║   ██║██████╔╝███████╗
██║███╗██║██║ ███╔╝  ██║   ██║██╔═══╝ ╚════██║
╚███╔███╔╝██║███████╗╚██████╔╝██║     ███████║
 ╚══╝╚══╝ ╚═╝╚══════╝ ╚═════╝ ╚═╝     ╚══════╝

        Linux Wizardry Operations Console
────────────────────────────────────────────────────────
"""

    PENDING = 0
    RUNNING = 1
    DONE = 2

    def __init__(self):
        self.tasks = []
        self.current = None

        self._running = False
        self._thread = None
        self._frame = " "

    def add(self, text: str):
        self.tasks.append([text, self.PENDING])

    def start(self, index: int):
        if self.current is not None:
        
            self.tasks[self.current][1] = self.DONE
            self.current = index
            self.tasks[index][1] = self.RUNNING

        if not self._running:
            print("\033[?25l", end="", flush=True)  # Hide cursor

            self._running = True
            self._thread = threading.Thread(
                target=self._spin,
                daemon=True,
            )
            self._thread.start()

        self._draw()

    def done(self):
        if self.current is not None:
            self.tasks[self.current][1] = self.DONE
            self.current = None

        self._draw()

    def stop(self):
        self._running = False

        if self._thread:
            self._thread.join()

        self._draw()
        
        print("\033[?25h", end="", flush=True)  # Show cursor
        
        time.sleep(0.25)

    def _spin(self):
        while self._running:
            self._frame = next(SPINNER)
            self._draw()
            time.sleep(0.08)

    def _draw(self):
        print("\033[2J\033[H", end="")

        print(self.LOGO)

        for text, state in self.tasks:

            if state == self.PENDING:
                icon = "○"

            elif state == self.RUNNING:
                icon = self._frame

            else:
                icon = "✓"

            print(f" {icon} {text}")

        sys.stdout.flush()
