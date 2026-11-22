import math
import random
import unittest
from curie.rela import Resonance
from curie.gates import H, X, SPLIT, phase
from curie.qstate import (zeros, basis, from_amplitudes, apply_1q, cnot, cz,
                          swap, ry, measure_qubit, sample)
from curie.entangle import bell


class StateTests(unittest.TestCase):
    def test_ordering_and_x(self):
        self.assertEqual(basis(3, '100').probabilities(), [0, 0, 0, 0, 1, 0, 0, 0])
        self.assertEqual(zeros(3).probabilities(), [1, 0, 0, 0, 0, 0, 0, 0])
        for q, bits in enumerate(('100', '010', '001')):
            self.assertTrue(apply_1q(zeros(3), X, q).isclose(basis(3, bits)))

    def test_bell_and_collapse(self):
        state = cnot(apply_1q(zeros(2), H, 0), 0, 1)
        p = state.probabilities()
        self.assertEqual(p[1:3], [0.0, 0.0])
        self.assertAlmostEqual(p[0], .5, delta=1e-12)
        self.assertAlmostEqual(p[3], .5, delta=1e-12)
        self.assertTrue(state.isclose(bell('phi+')))
        rng = random.Random(2024)
        counts = [0, 0]
        for _ in range(1000):
            a, collapsed = measure_qubit(state, 0, rng)
            b, collapsed = measure_qubit(collapsed, 1, rng)
            self.assertEqual(a, b)
            self.assertAlmostEqual(collapsed.norm(), 1)
            counts[a] += 1
        print('q1 collapse seed 2024:', counts)
        counts = sample(state, 1000, random.Random(2024))
        print('q1 sample seed 2024:', counts)
        self.assertLessEqual(set(counts), {'00', '11'})
        self.assertEqual(sum(counts.values()), 1000)

    def test_tensor_and_cap(self):
        a, b = apply_1q(zeros(1), H, 0), apply_1q(zeros(1), X, 0)
        self.assertTrue(a.tensor(b).isclose(apply_1q(apply_1q(zeros(2), H, 0), X, 1)))
        self.assertFalse(a.tensor(b).isclose(b.tensor(a)))
        with self.assertRaisesRegex(ValueError, '12 qubits'):
            zeros(13)
        for values in ([1, 0, 0], [2, 0]):
            with self.assertRaises(ValueError):
                from_amplitudes(values)
        self.assertTrue(from_amplitudes([1j, 0]).isclose(from_amplitudes([Resonance(1, math.pi / 2), 0])))

    def test_random_norms(self):
        rng = random.Random(1234)
        for _ in range(200):
            state = zeros(3)
            for _ in range(20):
                op = rng.randrange(8)
                q = rng.randrange(3)
                if op < 5:
                    gate = (H, X, SPLIT, phase(rng.uniform(-math.pi, math.pi)), ry(rng.uniform(-math.pi, math.pi)))[op]
                    state = apply_1q(state, gate, q)
                else:
                    other = (q + rng.randrange(1, 3)) % 3
                    state = (cnot, cz, swap)[op - 5](state, q, other)
                self.assertLess(abs(state.norm() - 1), 1e-9)
