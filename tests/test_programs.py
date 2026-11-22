import cmath
import math
import random
import unittest
from curie.programs import *
from curie.qstate import measure_qubit
from curie.rela import isclose


class ProgramsTests(unittest.TestCase):
    def assert_amps(self, actual, expected):
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a.real, b.real, delta=1e-12)
            self.assertAlmostEqual(a.imag, b.imag, delta=1e-12)

    def test_teleport_branches(self):
        s = 1 / math.sqrt(2)
        for a, b in [(1, 0), (0, 1), (s, s), (s, 1j*s),
                     (math.cos(.3), math.sin(.3)*cmath.exp(1.1j))]:
            start = from_amplitudes((a, 0, 0, 0, b, 0, 0, 0))
            before, _ = run(teleport_circuit()[:4], start)
            for m0 in range(2):
                for m1 in range(2):
                    one, p0 = project(before, 0, m0)
                    two, p1 = project(one, 1, m1)
                    self.assertAlmostEqual(p0*p1, .25, delta=1e-12)
                    expected = {(0, 0):(a, b), (0, 1):(b, a),
                                (1, 0):(a, -b), (1, 1):(-b, a)}[m0, m1]
                    self.assert_amps(qubit_amplitudes(two, 2), expected)
                    final, bits = teleport(a, b, forced={'m0':m0, 'm1':m1})
                    self.assertEqual(bits, (m0, m1))
                    self.assert_amps(qubit_amplitudes(final, 2), (a, b))

    def test_negative_control_and_project(self):
        s = 1/math.sqrt(2)
        state = from_amplitudes((s, 0, 0, 0, s, 0, 0, 0))
        final, _ = run(teleport_circuit()[:-1], state, forced={'m0':1, 'm1':0})
        self.assertFalse(isclose(qubit_amplitudes(final, 2)[1], from_amplitudes((s,s)).amps[1], 1e-12))
        with self.assertRaises(ValueError):
            project(zeros(1), 0, 1)
        for seed in range(10):
            bit, measured = measure_qubit(from_amplitudes((s, s)), 0, random.Random(seed))
            projected, _ = project(from_amplitudes((s, s)), 0, bit)
            self.assertTrue(measured.isclose(projected, 1e-12))

    def test_dj(self):
        funcs = {1:[lambda a:a, lambda a:1-a],
                 2:[lambda a,b:a, lambda a,b:b, lambda a,b:a^b, lambda a,b:1-a],
                 3:[lambda a,b,c:a, lambda a,b,c:c, lambda a,b,c:a^b^c,
                    lambda a,b,c:int(a+b+c >= 2), lambda a,b,c:int(a+b+c <= 1)]}
        for n in (1, 2, 3):
            for f, expected in [(lambda *x:0, 1), (lambda *x:1, 1)] + [(f, 0) for f in funcs[n]]:
                for oracle in ('xor', 'phase'):
                    verdict, p = deutsch_jozsa(f, n, oracle)
                    self.assertAlmostEqual(p, expected, delta=1e-12)
                    self.assertEqual(verdict, 'constant' if expected else 'balanced')
                    self.assertEqual(sum(op.startswith('oracle_') for op, _ in dj_circuit(truth_table(f,n), n, oracle)), 1)
        for f in (lambda a,b:a and b, lambda a,b:2):
            with self.assertRaises(ValueError):
                deutsch_jozsa(f, 2)

    def test_grover(self):
        self.assertEqual(optimal_iterations(2), 1)
        self.assertEqual(optimal_iterations(3), 2)
        for n, values in [(1, [.5]*4), (2, [.25, 1, .25, .25]),
                          (3, [1/8, 25/32, 121/128, 169/512, 25/2048])]:
            for marked in range(2**n):
                for k, expected in enumerate(values):
                    self.assertAlmostEqual(grover_probability(n, marked, k), expected, delta=1e-12)
                if n == 3:
                    state, _ = run(grover_circuit(n, marked, 2), zeros(n))
                    for i, a in enumerate(state.amps):
                        if i != marked:
                            self.assertAlmostEqual(a.intensity, 1/128, delta=1e-12)
        self.assertLess(grover_probability(3, 0, 3), grover_probability(3, 0, 2))
        with self.assertRaises(ValueError):
            grover_circuit(3, 8, 1)

    def test_mcz(self):
        for values in [(1,0,0,0), (0,0,0,1), (.5,.5,.5,.5), (.5,.5j,-.5,-.5j)]:
            state = from_amplitudes(values)
            self.assertTrue(mcz(state, (0,1)).isclose(cz(state, 0, 1), 1e-12))


if __name__ == '__main__':
    unittest.main()
