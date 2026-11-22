"""Discrete Fourier transforms built from resonance interference."""
import math
from .rela import Resonance, interfere_all


def twiddle(j: int, k: int, n: int, sign: int = -1) -> Resonance:
    return Resonance(1, sign * 2 * math.pi * ((j * k) % n) / n)


def dft(samples: list[Resonance]) -> list[Resonance]:
    n = len(samples)
    return [interfere_all(x * twiddle(j, k, n) for j, x in enumerate(samples))
            for k in range(n)]


def idft(spectrum: list[Resonance]) -> list[Resonance]:
    n = len(spectrum)
    return [interfere_all(x * twiddle(j, k, n, 1) for k, x in enumerate(spectrum)) * (1 / n)
            for j in range(n)]


def from_real(xs: list[float]) -> list[Resonance]:
    return [Resonance(abs(x), math.pi if x < 0 else 0) for x in xs]


def tone(n, m, amp=1.0, complex_=False) -> list[Resonance]:
    if complex_:
        return [Resonance(amp, 2 * math.pi * m * j / n) for j in range(n)]
    return from_real([amp * math.cos(2 * math.pi * m * j / n) for j in range(n)])


def spectrum(samples) -> list[float]:
    return [x.intensity for x in dft(samples)]
