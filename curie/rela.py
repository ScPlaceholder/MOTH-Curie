"""Polar resonance arithmetic and transformations.

Linear gates commute; order dependence arises with antilinear conjugation.
"""
import math
from dataclasses import dataclass
from numbers import Real
from typing import NamedTuple


@dataclass(frozen=True)
class Resonance:
    r: float
    theta: float

    def __post_init__(self):
        if self.r < 0:
            raise ValueError("radius must be nonnegative")
        t = math.fmod(self.theta, 2 * math.pi)
        if t <= -math.pi:
            t += 2 * math.pi
        elif t > math.pi:
            t -= 2 * math.pi
        object.__setattr__(self, "theta", 0.0 if self.r == 0 else t)

    @property
    def intensity(self):
        return self.r ** 2

    @property
    def real(self):
        return self.r * math.cos(self.theta)

    @property
    def imag(self):
        return self.r * math.sin(self.theta)

    @classmethod
    def from_xy(cls, x, y):
        return cls(math.hypot(x, y), math.atan2(y, x))

    def __mul__(self, other):
        if isinstance(other, Resonance):
            return Resonance(self.r * other.r, self.theta + other.theta)
        if isinstance(other, Real):
            return Resonance(self.r * abs(other), self.theta + (math.pi if other < 0 else 0))
        return NotImplemented

    __rmul__ = __mul__


ZERO = Resonance(0, 0)
ONE = Resonance(1, 0)


def isclose(a, b, tol=1e-9):
    return (math.isclose(a.real, b.real, rel_tol=0, abs_tol=tol)
            and math.isclose(a.imag, b.imag, rel_tol=0, abs_tol=tol))


class InterferenceReport(NamedTuple):
    result: Resonance
    alignment: float
    gain: float


_TRACE_HOOK = None  # set only by curie.trace; None = tracing off

def interfere(a, b):
    result = Resonance.from_xy(a.real + b.real, a.imag + b.imag)
    alignment = math.cos(a.theta - b.theta) if a.r and b.r else 1.0
    report = InterferenceReport(result, alignment,
                                result.intensity - (a.intensity + b.intensity))
    if _TRACE_HOOK is not None:
        _TRACE_HOOK(a, b, report)
    return report


def interfere_all(values):
    result = ZERO
    for value in values:
        result = interfere(result, value).result
    return result


def rotate(phi):
    return gate(1, phi)


def scale(k):
    if k < 0:
        raise ValueError("scale must be nonnegative")
    return gate(k, 0)


def gate(r, theta):
    factor = Resonance(r, theta)
    return lambda value: value * factor


def conjugate(value):
    return Resonance(value.r, -value.theta)


def compose(*fs):
    def transform(value):
        for f in fs:
            value = f(value)
        return value
    return transform

# Polar-native operations are attached here to preserve the original class.
from numbers import Integral


def _inverse(self):
    if self.r == 0:
        raise ZeroDivisionError("inverse of zero resonance")
    return Resonance(1 / self.r, -self.theta)


def _truediv(self, other):
    if isinstance(other, Resonance):
        if other.r == 0:
            raise ZeroDivisionError("division by zero resonance")
        return Resonance(self.r / other.r, self.theta - other.theta)
    if isinstance(other, Real):
        return self * (1 / other)
    return NotImplemented


def _rtruediv(self, other):
    if not isinstance(other, Real):
        return NotImplemented
    return other * self.inverse()


def _pow(self, n):
    if not isinstance(n, Integral):
        return NotImplemented
    if n == 0:
        return ONE
    if n < 0:
        return self.inverse() ** (-n)
    return Resonance(self.r ** n, n * self.theta)


def _roots(self, n):
    if not isinstance(n, Integral) or n < 1:
        raise ValueError("root count must be a positive integer")
    if self.r == 0:
        return [ZERO] * n
    return [Resonance(self.r ** (1 / n), (self.theta + 2 * math.pi * k) / n)
            for k in range(n)]


def _principal_root(self, n):
    return self.roots(n)[0]


Resonance.inverse = _inverse
Resonance.__truediv__ = _truediv
Resonance.__rtruediv__ = _rtruediv
Resonance.__pow__ = _pow
Resonance.roots = _roots
Resonance.principal_root = _principal_root
