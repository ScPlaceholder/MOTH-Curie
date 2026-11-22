"""Synchronous resonance graphs and example factories."""
import math
from .rela import ZERO, ONE, gate, interfere_all, rotate


class EventGraph:
    def __init__(self):
        self._values = {}
        self._incoming = {}

    def add_node(self, name, value=ZERO):
        self._values[name] = value
        self._incoming.setdefault(name, [])

    def add_edge(self, src, dst, transform):
        if src not in self._values or dst not in self._values:
            raise KeyError((src, dst))
        self._incoming[dst].append((src, transform))

    def step(self):
        old = self._values
        self._values = {node: interfere_all(transform(old[src]) for src, transform in edges)
                        for node, edges in self._incoming.items()}

    def run(self, n):
        for _ in range(n):
            self.step()

    @property
    def values(self):
        return self._values.copy()


def total_intensity(graph):
    return sum(value.intensity for value in graph.values.values())


def observe(graph):
    values = graph.values
    total = sum(value.intensity for value in values.values())
    return {name: value.intensity / total if total else 0.0
            for name, value in values.items()}


def ring(n=4, phi=math.pi / 2):
    graph = EventGraph()
    for i in range(n):
        graph.add_node(i, ONE if i == 0 else ZERO)
    for i in range(n):
        graph.add_edge(i, (i + 1) % n, rotate(phi))
    return graph


def interferometer(phi):
    graph = EventGraph()
    for name in ("S", "A", "B", "D1", "D2"):
        graph.add_node(name, ONE if name == "S" else ZERO)
    s = 1 / math.sqrt(2)
    for src, dst, theta in (("S", "A", 0), ("S", "B", math.pi / 2),
                            ("A", "D1", math.pi / 2), ("A", "D2", 0),
                            ("B", "D1", phi), ("B", "D2", phi + math.pi / 2)):
        graph.add_edge(src, dst, gate(s, theta))
    return graph
