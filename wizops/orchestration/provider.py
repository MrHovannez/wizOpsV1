from __future__ import annotations

from abc import ABC, abstractmethod

from .models import CollectorPage, CollectorRequest


class CollectionProvider(ABC):

    @abstractmethod
    def fetch(
        self,
        request: CollectorRequest,
    ) -> CollectorPage:
        """Return one page of collected data."""
