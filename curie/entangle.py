"""Entangled states and correlations in the most-significant-qubit-first basis."""
import math
from .rela import interfere
from .gates import H
from .qstate import zeros, basis, apply_1q, cnot, ry, sample, _mask


def bell(kind):
    starts = {'phi+': '00', 'phi-': '10', 'psi+': '01', 'psi-': '11'}
    if kind not in starts:
        raise ValueError("kind must be one of phi+, phi-, psi+, psi-")
    return cnot(apply_1q(basis(2, starts[kind]), H, 0), 0, 1)


def ghz(n):
    state = apply_1q(zeros(n), H, 0)
    for q in range(1, n):
        state = cnot(state, 0, q)
    return state


def reduced_probabilities(state, q):
    mask = _mask(state, q)
    return (sum(a.intensity for i, a in enumerate(state.amps) if not i & mask),
            sum(a.intensity for i, a in enumerate(state.amps) if i & mask))


def is_product_state(state, tol=1e-9):
    if state.n != 2:
        raise ValueError("product test requires two qubits")
    a, b, c, d = state.amps
    return interfere(a * d, (b * c) * -1).result.r <= tol


def correlation(state, a, b):
    if state.n != 2:
        raise ValueError("correlation requires two qubits")
    rotated = apply_1q(apply_1q(state, ry(-a), 0), ry(-b), 1)
    p = rotated.probabilities()
    return p[0] - p[1] - p[2] + p[3]


CHSH_ANGLES = (0, math.pi / 2, math.pi / 4, -math.pi / 4)


def chsh_value(state):
    """Return CHSH S using angles optimal for phi+."""
    a0, a1, b0, b1 = CHSH_ANGLES
    return (correlation(state, a0, b0) + correlation(state, a0, b1)
            + correlation(state, a1, b0) - correlation(state, a1, b1))


def chsh_sampled(state, shots, rng):
    if state.n != 2 or shots <= 0:
        raise ValueError("sampling requires two qubits and positive shots")
    a0, a1, b0, b1 = CHSH_ANGLES
    def estimate(a, b):
        rotated = apply_1q(apply_1q(state, ry(-a), 0), ry(-b), 1)
        counts = sample(rotated, shots, rng)
        return (counts.get('00', 0) + counts.get('11', 0)
                - counts.get('01', 0) - counts.get('10', 0)) / shots
    return estimate(a0, b0) + estimate(a0, b1) + estimate(a1, b0) - estimate(a1, b1)
