"""Two-mode linear gates: unlike scalar gates, these can fail to commute."""
import math
from dataclasses import dataclass
from .rela import Resonance, ZERO, ONE, interfere, interfere_all, isclose


@dataclass(frozen=True)
class Gate:
    m: tuple[tuple[Resonance, Resonance], tuple[Resonance, Resonance]]

    @classmethod
    def from_rows(cls, a, b, c, d):
        return cls(((a, b), (c, d)))

    def apply(self, state):
        return tuple(interfere(row[0] * state[0], row[1] * state[1]).result
                     for row in self.m)

    __call__ = apply

    def __matmul__(self, other):
        if not isinstance(other, Gate):
            return NotImplemented
        return Gate(tuple(tuple(interfere_all(self.m[i][k] * other.m[k][j]
                                               for k in range(2))
                                for j in range(2)) for i in range(2)))

    def then(self, other):
        return other @ self

    def isclose(self, other, tol=1e-9):
        return all(isclose(self.m[i][j], other.m[i][j], tol)
                   for i in range(2) for j in range(2))


def intensities(state):
    return tuple(value.intensity for value in state)


def norm(state):
    return sum(intensities(state))


IDENTITY = Gate.from_rows(ONE, ZERO, ZERO, ONE)
X = Gate.from_rows(ZERO, ONE, ONE, ZERO)
s = 1 / math.sqrt(2)
SPLIT = Gate.from_rows(Resonance(s, 0), Resonance(s, math.pi / 2),
                       Resonance(s, math.pi / 2), Resonance(s, 0))
H = Gate.from_rows(Resonance(s, 0), Resonance(s, 0),
                   Resonance(s, 0), Resonance(s, math.pi))


def phase(phi):
    return Gate.from_rows(ONE, ZERO, ZERO, Resonance(1, phi))


def interferometer(phi):
    return SPLIT.then(phase(phi)).then(SPLIT)
