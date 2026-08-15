from abc import ABC, abstractmethod


class InventoryProvider(ABC):

    @abstractmethod
    def snapshot(self):
        """Return an inventory snapshot."""
        raise NotImplementedError
