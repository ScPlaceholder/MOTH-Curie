"""Cross-check Curie against an outside simulator (Qiskit's exact Statevector).

Skipped when qiskit is not installed, so the core suite never depends on it.
Run it alone for numbers:  python tests/test_xcheck_qiskit.py

Conventions, the thing this file exists to catch:
- Curie puts qubit 0 on the LEFTMOST bit of a basis index (q0 is the MSB).
- Qiskit puts qubit 0 on the RIGHTMOST bit (little-endian).
So index i in Curie is index reverse_bits(i) in Qiskit. Comparing without the reversal must FAIL on
asymmetric circuits; test_ordering_is_load_bearing proves that, so a green run cannot come from the
reversal being a no-op.
- Gates are compared EXACTLY, not up to global phase: Curie's H, X, Z, phase(phi)=diag(1,e^{i phi}),
  ry(theta)=[[c,-s],[s,c]], CNOT, CZ and SWAP are the same matrices as Qiskit's h, x, z, p, ry, cx, cz, swap.
"""
import math, os, random, sys

import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
# unittest.SkipTest, not pytest.importorskip: both runners honour it, so `python -m unittest` skips this
# file cleanly when Qiskit is absent instead of reporting an import error. (The tests below are plain
# pytest-style functions, so the cross-check itself runs under pytest.)
try:
    import qiskit
except ImportError:
    raise unittest.SkipTest('qiskit is not installed; the Qiskit cross-check is skipped')
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit.circuit.library import UnitaryGate, ZGate

from curie import programs
from curie.qstate import zeros

TOL = 1e-9


def reverse_bits(i, n):
    return int(format(i, '0%db' % n)[::-1], 2)


def curie_vector(circuit, n):
    state, _ = programs.run(circuit, zeros(n))
    return np.array([a.r * complex(math.cos(a.theta), math.sin(a.theta)) for a in state.amps])


def _diag_in_qiskit_order(n, signs_curie_order):
    d = np.empty(2 ** n, dtype=complex)
    for i, s in enumerate(signs_curie_order):
        d[reverse_bits(i, n)] = s
    return np.diag(d)


def qiskit_vector(circuit, n):
    qc = QuantumCircuit(n)
    for name, args in circuit:
        if name == 'h': qc.h(args[0])
        elif name == 'x': qc.x(args[0])
        elif name == 'z': qc.z(args[0])
        elif name == 'phase': qc.p(args[1], args[0])
        elif name == 'ry': qc.ry(args[1], args[0])
        elif name == 'cnot': qc.cx(args[0], args[1])
        elif name == 'cz': qc.cz(args[0], args[1])
        elif name == 'swap': qc.swap(args[0], args[1])
        elif name == 'mcz':
            qs = list(args[0])
            if len(qs) == 1: qc.z(qs[0])
            else: qc.append(ZGate().control(len(qs) - 1), qs)
        elif name == 'flip':
            signs = [-1 if i == args[0] else 1 for i in range(2 ** n)]
            qc.append(UnitaryGate(_diag_in_qiskit_order(n, signs)), list(range(n)))
        elif name == 'oracle_phase':
            inputs, table = args
            signs = []
            for i in range(2 ** n):
                key = 0
                for q in inputs:
                    key = (key << 1) | ((i >> (n - 1 - q)) & 1)
                signs.append(-1 if table[key] else 1)
            qc.append(UnitaryGate(_diag_in_qiskit_order(n, signs)), list(range(n)))
        else:
            raise ValueError('no Qiskit mapping for ' + name)
    return np.asarray(Statevector.from_instruction(qc).data)


def in_curie_order(vec_qiskit, n):
    return np.array([vec_qiskit[reverse_bits(i, n)] for i in range(2 ** n)])


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
    return float(np.max(np.abs(curie_vector(circuit, n) - in_curie_order(qiskit_vector(circuit, n), n))))


def test_random_circuits_match_qiskit_exactly():
    rng = random.Random(20261121)
    worst = 0.0
    for _ in range(300):
        n = rng.randint(1, 5)
        c = random_circuit(rng, n, rng.randint(1, 30))
        worst = max(worst, worst_gap(c, n))
    assert worst < TOL, worst


def test_programs_match_qiskit():
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


def test_ordering_is_load_bearing():
    """Without the bit reversal, an asymmetric circuit must disagree, or this file proves nothing.
    (The first version used x0, h1, cnot 0-2, whose answers 101/111 are palindromes: reversal is a no-op
    there, and this test correctly refused it.)"""
    c, n = [('x', (0,)), ('h', (1,))], 3   # answers 100/110; reversed they read 001/011
    naive = float(np.max(np.abs(curie_vector(c, n) - qiskit_vector(c, n))))
    assert naive > 0.1, naive
    assert worst_gap(c, n) < TOL


def test_reversal_matters_across_the_random_set():
    """Most random circuits must DISAGREE with Qiskit if the reversal is dropped."""
    rng = random.Random(20261121)
    differ = total = 0
    for _ in range(300):
        n = rng.randint(1, 5)
        c = random_circuit(rng, n, rng.randint(1, 30))
        if n > 1:
            total += 1
            naive = float(np.max(np.abs(curie_vector(c, n) - qiskit_vector(c, n))))
            differ += naive > 1e-6
    assert differ > 0.5 * total, (differ, total)


if __name__ == '__main__':
    rng = random.Random(20261121)
    worst, count, gates = 0.0, 0, 0
    for _ in range(300):
        n = rng.randint(1, 5)
        c = random_circuit(rng, n, rng.randint(1, 30))
        worst = max(worst, worst_gap(c, n)); count += 1; gates += len(c)
    print('random circuits: %d (%d gates, 1-5 qubits), worst |Curie - Qiskit| = %.2e' % (count, gates, worst))
    test_programs_match_qiskit(); print('Deutsch-Jozsa x3 and Grover x3: match')
    c, n = [('x', (0,)), ('h', (1,))], 3   # answers 100/110; reversed they read 001/011
    print('without bit reversal the same check reads %.3f (so the ordering mapping is doing real work)'
          % float(np.max(np.abs(curie_vector(c, n) - qiskit_vector(c, n)))))
