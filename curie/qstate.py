"""N-qubit states: qubit 0 is the most significant bit; bitstrings index in base 2."""
import math
from dataclasses import dataclass
from .rela import Resonance, ZERO, ONE, isclose
from .gates import Gate, X, phase
from .measure import _choose, probabilities

MAX_QUBITS = 12


def _size(n):
    if not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer")
    if n > MAX_QUBITS:
        raise ValueError(f"Curie stores all 2**n amplitudes and touches every one on each gate (O(2**n)); n={n} needs {2**n}. The limit is {MAX_QUBITS} qubits.")
    return 2**n


def _mask(state, q):
    if not isinstance(q, int) or not 0 <= q < state.n:
        raise ValueError("qubit index out of range")
    return 1 << (state.n - 1 - q)


@dataclass(frozen=True)
class State:
    n: int
    amps: tuple[Resonance, ...]

    def __post_init__(self):
        if len(self.amps) != _size(self.n):
            raise ValueError("amplitude count must equal 2**n")
        if not isinstance(self.amps, tuple) or not all(isinstance(a, Resonance) for a in self.amps):
            raise ValueError("amps must be a tuple of Resonance values")

    def probabilities(self):
        return [a.intensity for a in self.amps]

    def norm(self):
        return sum(self.probabilities())

    def tensor(self, other):
        _size(self.n + other.n)
        return State(self.n + other.n, tuple(a * b for a in self.amps for b in other.amps))

    def isclose(self, other, tol=1e-9):
        """Compare amplitudes; global phase counts as a difference."""
        return self.n == other.n and all(isclose(a, b, tol) for a, b in zip(self.amps, other.amps))


def zeros(n):
    return State(n, (ONE,) + (ZERO,) * (_size(n) - 1))


def basis(n, bits):
    size = _size(n)
    if not isinstance(bits, str) or len(bits) != n or any(b not in '01' for b in bits):
        raise ValueError("bits must contain exactly n binary digits")
    amps = [ZERO] * size
    amps[int(bits, 2)] = ONE
    return State(n, tuple(amps))


def from_amplitudes(values, tol=1e-9):
    values = tuple(values)
    length = len(values)
    if length < 2 or length & (length - 1):
        raise ValueError("amplitude count must be a power of two and at least two")
    n = length.bit_length() - 1
    _size(n)
    amps = tuple(v if isinstance(v, Resonance) else Resonance.from_xy(v.real, v.imag)
                 if isinstance(v, (int, float, complex)) else _bad_amplitude() for v in values)
    state = State(n, amps)
    norm = state.norm()
    if not math.isfinite(norm) or abs(norm - 1) > tol:
        raise ValueError(f"amplitude norm is {norm}, expected 1")
    return state


def _bad_amplitude():
    raise TypeError("amplitudes must be Resonance or numbers")


def apply_1q(state, gate, target):
    """Apply a single-qubit gate in O(2**n) per gate."""
    mask = _mask(state, target)
    amps = list(state.amps)
    for i in range(len(amps)):
        if not i & mask:
            amps[i], amps[i | mask] = gate.apply((state.amps[i], state.amps[i | mask]))
    return State(state.n, tuple(amps))


def controlled(state, gate, control, target):
    """Apply a controlled gate in O(2**n) per gate."""
    cmask, tmask = _mask(state, control), _mask(state, target)
    if control == target:
        raise ValueError("control and target must differ")
    amps = list(state.amps)
    for i in range(len(amps)):
        if i & cmask and not i & tmask:
            amps[i], amps[i | tmask] = gate.apply((state.amps[i], state.amps[i | tmask]))
    return State(state.n, tuple(amps))


def cnot(state, control, target):
    """Apply CNOT in O(2**n) per gate."""
    return controlled(state, X, control, target)


def cz(state, control, target):
    """Apply CZ in O(2**n) per gate."""
    return controlled(state, phase(math.pi), control, target)


def swap(state, i, j):
    """Swap two qubits in O(2**n) per gate."""
    imask, jmask = _mask(state, i), _mask(state, j)
    amps = [ZERO] * len(state.amps)
    for k, a in enumerate(state.amps):
        dest = k ^ (imask | jmask) if bool(k & imask) != bool(k & jmask) else k
        amps[dest] = a
    return State(state.n, tuple(amps))


def ry(theta):
    """Construct a Y rotation; application takes O(2**n) per gate."""
    def polar(x):
        return Resonance(abs(x), math.pi if x < 0 else 0)
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    return Gate.from_rows(polar(c), polar(-s), polar(s), polar(c))


def measure_qubit(state, q, rng):
    mask = _mask(state, q)
    p1 = sum(a.intensity for i, a in enumerate(state.amps) if i & mask)
    p0 = max(0.0, 1 - p1)
    bit = _choose(probabilities([p0, p1]), rng)
    p = (p0, p1)[bit]
    return bit, State(state.n, tuple(a * (1 / math.sqrt(p)) if bool(i & mask) == bool(bit) else ZERO
                                    for i, a in enumerate(state.amps)))


def measure_all(state, rng):
    return format(_choose(probabilities(state.probabilities()), rng), f'0{state.n}b')


def sample(state, shots, rng):
    counts = {}
    for _ in range(shots):
        bits = measure_all(state, rng)
        counts[bits] = counts.get(bits, 0) + 1
    return counts
