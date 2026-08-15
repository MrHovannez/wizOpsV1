from .base import EventSource


class CompositeEventSource(EventSource):

    def __init__(self, *sources):
        self.sources = list(sources)

    def list_events(self):
        return self.sources[0].list_events()

    def search_events(self, where, params):
        return self.sources[0].search_events(where, params)
