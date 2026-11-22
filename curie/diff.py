"""Compare circuit checkpoints up to global phase."""
import cmath
from typing import NamedTuple
from .programs import run


class DiffResult(NamedTuple):
    equivalent: bool
    where: object
    phase: float
    max_dev: float


def _complex(a):
    return complex(a.real, a.imag)


def equal_up_to_phase(a, b, tol=1e-9):
    a, b = [_complex(x) for x in a], [_complex(x) for x in b]
    if not a or len(a) != len(b):
        raise ValueError('amplitude lists must have equal nonzero length')
    m = max(range(len(a)), key=lambda i: abs(a[i]))
    if abs(a[m]) <= tol or abs(b[m]) <= tol:
        return False, 0.0, max(abs(x-y) for x, y in zip(a, b))
    u = b[m] / abs(b[m]) * (a[m] / abs(a[m])).conjugate()
    deviation = max(abs(u*x-y) for x, y in zip(a, b))
    return deviation <= tol, cmath.phase(u), deviation


def diff(circ_a, circ_b, initial, checkpoints=None, tol=1e-9):
    a, b = list(circ_a), list(circ_b)
    if checkpoints is None:
        checkpoints = [(k, k+1, k+1) for k in range(len(a))] if len(a) == len(b) else [('end', len(a), len(b))]
        if not checkpoints:
            checkpoints = [('end', 0, 0)]
    checkpoints = list(checkpoints)
    prev_i = prev_j = -1
    for name, i, j in checkpoints:
        if not isinstance(i, int) or not isinstance(j, int) or not (0 <= i <= len(a) and 0 <= j <= len(b)) or i <= prev_i or j <= prev_j:
            raise ValueError('checkpoint indices must strictly increase and be in range')
        prev_i, prev_j = i, j
    sa = sb = initial
    ia = ib = 0
    phase = deviation = 0.0
    for name, i, j in checkpoints:
        sa, _ = run(a[ia:i], sa)
        sb, _ = run(b[ib:j], sb)
        ia, ib = i, j
        equal, phase, deviation = equal_up_to_phase(sa.amps, sb.amps, tol)
        if not equal:
            return DiffResult(False, name, phase, deviation)
    return DiffResult(True, None, phase, deviation)
