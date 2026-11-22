"""Born-rule sampling for two-mode states and graph observations."""
import random
from typing import Sequence
from .rela import Resonance, ZERO


def probabilities(weights: Sequence[float]) -> list[float]:
    if any(weight < 0 for weight in weights):
        raise ValueError("weights must be nonnegative")
    total = sum(weights)
    if total == 0:
        raise ValueError("total weight must be positive")
    return [weight / total for weight in weights]


def _choose(probs, rng) -> int:
    u = rng.random()
    cumulative = 0.0
    last = None
    for i, p in enumerate(probs):
        cumulative += p
        if p > 0:
            last = i
            if u < cumulative:
                return i
    if last is None:
        raise ValueError("no positive probability")
    return last


def measure(state: tuple[Resonance, Resonance], rng: random.Random) -> tuple[int, tuple[Resonance, Resonance]]:
    """Choose a port, preserving its phase and setting its collapsed radius to 1."""
    k = _choose(probabilities([value.intensity for value in state]), rng)
    collapsed = [ZERO, ZERO]
    collapsed[k] = Resonance(1, state[k].theta)
    return k, tuple(collapsed)


def sample(state, shots: int, rng) -> tuple[int, int]:
    counts = [0, 0]
    for _ in range(shots):
        counts[measure(state, rng)[0]] += 1
    return tuple(counts)


def measure_graph(observed: dict[str, float], rng) -> str:
    names = list(observed)
    return names[_choose(probabilities(list(observed.values())), rng)]
