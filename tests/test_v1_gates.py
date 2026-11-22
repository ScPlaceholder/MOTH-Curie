import math
import random
import unittest
from curie.rela import Resonance, ZERO, ONE, isclose, compose
from curie import graph
from curie.gates import Gate, IDENTITY, X, H, SPLIT, phase, interferometer, intensities, norm


class GateTests(unittest.TestCase):
    def assertState(self, a, b):
        for x, y in zip(a, b):
            self.assertTrue(isclose(x, y, 1e-9), (x, y))

    def test_g1_products(self):
        minus = Resonance(1, math.pi)
        self.assertTrue((X @ X).isclose(IDENTITY))
        self.assertTrue((H @ H).isclose(IDENTITY))
        self.assertTrue((SPLIT @ SPLIT @ SPLIT @ SPLIT).isclose(
            Gate.from_rows(minus, ZERO, ZERO, minus)))

    def test_g2_swap(self):
        self.assertState(X((ONE, ZERO)), (ZERO, ONE))

    def test_g3_noncommutation(self):
        p = phase(math.pi / 2)
        self.assertFalse((p @ X).isclose(X @ p))

    def test_g4_observable(self):
        s = 1 / math.sqrt(2)
        state = (Resonance(s, 0), Resonance(s, 0))
        for phi in (0, math.pi / 3, math.pi / 2, 2, math.pi):
            first = X.then(phase(phi)).then(SPLIT)(state)[0].intensity
            second = phase(phi).then(X).then(SPLIT)(state)[0].intensity
            self.assertAlmostEqual(first, (1 - math.sin(phi)) / 2, delta=1e-9)
            self.assertAlmostEqual(second, (1 + math.sin(phi)) / 2, delta=1e-9)

    def test_g5_graph(self):
        for phi in (0, math.pi / 3, math.pi / 2, 2, math.pi):
            ports = intensities(interferometer(phi)((ONE, ZERO)))
            g = graph.interferometer(phi)
            g.run(2)
            observed = graph.observe(g)
            for actual, expected in zip(ports, (math.sin(phi / 2) ** 2,
                                                 math.cos(phi / 2) ** 2)):
                self.assertAlmostEqual(actual, expected, delta=1e-9)
            self.assertAlmostEqual(ports[0], observed['D2'], delta=1e-9)
            self.assertAlmostEqual(ports[1], observed['D1'], delta=1e-9)

    def test_g6_norm(self):
        rng = random.Random(0)
        for _ in range(200):
            angle = rng.uniform(0, math.pi / 2)
            state = (Resonance(math.cos(angle), rng.uniform(-math.pi, math.pi)),
                     Resonance(math.sin(angle), rng.uniform(-math.pi, math.pi)))
            for _ in range(rng.randint(1, 30)):
                gate = rng.choice((IDENTITY, X, SPLIT, H, phase(rng.uniform(-math.pi, math.pi))))
                state = gate(state)
                self.assertAlmostEqual(norm(state), 1, delta=1e-9)

    def test_g7_composition(self):
        state = (Resonance(.6, .7), Resonance(.8, -1))
        gates = (X, phase(.7), SPLIT, H)
        matrix = IDENTITY
        for gate in gates:
            matrix = matrix.then(gate)
        self.assertState(matrix(state), compose(*gates)(state))
