from __future__ import annotations

from abc import ABC, abstractmethod


class EventSource(ABC):

    @abstractmethod
    def search_events(self, where: str, params: list):
        """Return events matching a query."""

    @abstractmethod
    def list_events(self):
        """Return all events."""
