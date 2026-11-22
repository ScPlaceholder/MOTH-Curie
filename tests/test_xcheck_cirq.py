"""Cross-check Curie against a second, independent simulator: Google's Cirq (exact state vector).

Skipped when cirq is not installed, so the core suite never depends on it.
Run it alone for numbers:  python tests/test_xcheck_cirq.py

Why a second simulator: Qiskit (test_xcheck_qiskit.py) is one implementation. Two independent
simulators agreeing with Curie, written by different teams with different conventions, is much stronger
evidence than one.

Conventions:
- Cirq's simulate() orders LineQubit(0) as the MOST significant bit, the same as Curie (q0 is the MSB),
  so NO bit reversal is applied here. That makes a silent convention bug easier to miss, not harder, so
  test_comparison_has_teeth proves the opposite: compare with a deliberate reversal and most circuits
  must DISAGREE. A green run therefore cannot come from a comparison that cannot fail.
- Gates are compared EXACTLY, not up to global phase. Curie's phase(phi) = diag(1, e^{i phi}) is Cirq's
  ZPowGate(exponent=phi/pi) with global_shift 0; Curie's ry(theta) = [[c,-s],[s,c]] is cirq.ry(theta).
  H, X, Z, CNOT, CZ and SWAP are the same matrices in both.
"""
import math, os, random, sys

import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
try:
    import cirq
except ImportError:
    raise unittest.SkipTest('cirq is not installed; the Cirq cross-check is skipped')
import numpy as np

from curie import programs
from curie.qstate import zeros

TOL = 1e-6   # Cirq simulates in complex64 by default; see _sim below, which asks for complex128.


def _sim():
    return cirq.Simulator(dtype=np.complex128)


def curie_vector(circuit, n):
    state, _ = programs.run(circuit, zeros(n))
    return np.array([a.r * complex(math.cos(a.theta), math.sin(a.theta)) for a in state.amps])


def cirq_vector(circuit, n):
    q = cirq.LineQubit.range(n)
    ops = []
    for name, args in circuit:
        if name == 'h': ops.append(cirq.H(q[args[0]]))
        elif name == 'x': ops.append(cirq.X(q[args[0]]))
        elif name == 'z': ops.append(cirq.Z(q[args[0]]))
        elif name == 'phase': ops.append(cirq.ZPowGate(exponent=args[1] / math.pi)(q[args[0]]))
        elif name == 'ry': ops.append(cirq.ry(args[1])(q[args[0]]))
        elif name == 'cnot': ops.append(cirq.CNOT(q[args[0]], q[args[1]]))
        elif name == 'cz': ops.append(cirq.CZ(q[args[0]], q[args[1]]))
        elif name == 'swap': ops.append(cirq.SWAP(q[args[0]], q[args[1]]))
        elif name == 'mcz':
            qs = [q[i] for i in args[0]]
            ops.append(cirq.Z(qs[0]) if len(qs) == 1 else cirq.Z(qs[-1]).controlled_by(*qs[:-1]))
        elif name == 'flip':
            d = np.array([-1 if i == args[0] else 1 for i in range(2 ** n)], dtype=complex)
            ops.append(cirq.MatrixGate(np.diag(d)).on(*q))
        elif name == 'oracle_phase':
            inputs, table = args
            signs = []
            for i in range(2 ** n):
                key = 0
                for b in inputs:
                    key = (key << 1) | ((i >> (n - 1 - b)) & 1)
                signs.append(-1 if table[key] else 1)
            ops.append(cirq.MatrixGate(np.diag(np.array(signs, dtype=complex))).on(*q))
        else:
            raise ValueError('no Cirq mapping for ' + name)
    c = cirq.Circuit(ops)
    # An empty or partial circuit must still act on every qubit, or Cirq returns a shorter vector.
    c.append(cirq.I.on_each(*q))
    return np.asarray(_sim().simulate(c, qubit_order=q).final_state_vector)


def reverse_bits(i, n):
    return int(format(i, '0%db' % n)[::-1], 2)


def random_circuit(rng, n, depth):
    out = []
    for _ in range(depth):
        kind = rng.choice(['h', 'x', 'z', 'phase', 'ry'] + (['cnot', 'cz', 'swap'] if n > 1 else []))
        if kind in ('h', 'x', 'z'):
            out.append((kind, (rng.randrange(n),)))
        elif kind in ('phase', 'ry'):
            out.append((kind, (rng.randrange(n), rng.uniform(-2 * math.pi, 2 * math.pi))))
        else:
            a, b = rng.sample(range(n), 2)
            out.append((kind, (a, b)))
    return out


def worst_gap(circuit, n):
    return float(np.max(np.abs(curie_vector(circuit, n) - cirq_vector(circuit, n))))


def test_random_circuits_match_cirq_exactly():
    rng = random.Random(20261122)   # a different seed from the Qiskit file, so this is a new sample
    worst = 0.0
    for _ in range(300):
        n = rng.randint(1, 5)
        c = random_circuit(rng, n, rng.randint(1, 30))
        worst = max(worst, worst_gap(c, n))
    assert worst < TOL, worst


def test_programs_match_cirq():
    cases = [
        (programs.dj_circuit((0, 1, 1, 0), 2, oracle='phase'), 2),
        (programs.dj_circuit((1, 1, 1, 1), 2, oracle='phase'), 2),
        (programs.dj_circuit((0, 1, 0, 1, 1, 0, 1, 0), 3, oracle='phase'), 3),
        (programs.grover_circuit(2, 3, 1), 2),
        (programs.grover_circuit(3, 5, programs.optimal_iterations(3)), 3),
        (programs.grover_circuit(4, 9, 2), 4),
    ]
    for c, n in cases:
        assert worst_gap(c, n) < TOL, (c[:3], n)


def test_comparison_has_teeth():
    """Compared with a deliberate bit reversal, most multi-qubit circuits must DISAGREE.
    If they did not, the comparison could not detect a convention bug and a pass would mean nothing."""
    rng = random.Random(20261122)
    differ = total = 0
    for _ in range(300):
        n = rng.randint(1, 5)
        c = random_circuit(rng, n, rng.randint(1, 30))
        if n > 1:
            total += 1
            v = cirq_vector(c, n)
            wrong = np.array([v[reverse_bits(i, n)] for i in range(2 ** n)])
            differ += float(np.max(np.abs(curie_vector(c, n) - wrong))) > 1e-3
    assert differ > 0.5 * total, (differ, total)


if __name__ == '__main__':
    rng = random.Random(20261122)
    worst, count, gates = 0.0, 0, 0
    for _ in range(300):
        n = rng.randint(1, 5)
        c = random_circuit(rng, n, rng.randint(1, 30))
        worst = max(worst, worst_gap(c, n)); count += 1; gates += len(c)
    print('cirq %s: random circuits %d (%d gates, 1-5 qubits), worst |Curie - Cirq| = %.2e'
          % (cirq.__version__, count, gates, worst))
    test_programs_match_cirq(); print('Deutsch-Jozsa x3 and Grover x3: match')
    test_comparison_has_teeth(); print('with a deliberate bit reversal, most circuits disagree (the check has teeth)')
