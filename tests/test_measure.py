import math
import random
import unittest
from curie.gates import interferometer, intensities
from curie.measure import _choose, measure, measure_graph, probabilities, sample
from curie.rela import ONE, ZERO, Resonance


class FixedRng:
    def __init__(self, value):
        self.value = value

    def random(self):
        return self.value


class MeasurementTests(unittest.TestCase):
    def state(self, phi):
        return interferometer(phi)((ONE, ZERO))

    def test_a_interferometer(self):
        for phi, expected in ((math.pi, (1, 0)), (0, (0, 1)), (math.pi / 2, (.5, .5))):
            for a, b in zip(intensities(self.state(phi)), expected):
                self.assertAlmostEqual(a, b, delta=1e-9)

    def test_b_seed(self):
        state = self.state(math.pi / 2)
        def outcomes():
            rng = random.Random(1234)
            return [measure(state, rng)[0] for _ in range(50)]
        self.assertEqual(outcomes(), outcomes())

    def test_c_deterministic(self):
        self.assertEqual(sample(self.state(math.pi), 1000, random.Random(1)), (1000, 0))
        self.assertEqual(sample(self.state(0), 1000, random.Random(1)), (0, 1000))

    def test_d_balanced(self):
        n0, n1 = sample(self.state(math.pi / 2), 10000, random.Random(2024))
        print(f"\nseed 2024: n0={n0}, n1={n1}")
        self.assertLessEqual(abs(n0 - 5000), 150)
        self.assertEqual(n0 + n1, 10000)

    def test_e_repeat(self):
        rng = random.Random(42)
        first, collapsed = measure(self.state(math.pi / 2), rng)
        self.assertTrue(all(measure(collapsed, rng)[0] == first for _ in range(100)))

    def test_f_zero_probability(self):
        rng = random.Random(8)
        self.assertEqual(sample((ZERO, Resonance(.3, 1)), 1000, rng), (0, 1000))
        self.assertTrue(all(measure_graph({'a': 0, 'b': 2, 'c': 0}, rng) == 'b' for _ in range(200)))
        for u in (0.0, .9999999999999999):
            self.assertEqual(_choose([0, .3, 0], FixedRng(u)), 1)

    def test_g_phase(self):
        state = (Resonance(.6, .7), Resonance(.8, -1))
        for u in (0, .9):
            chosen, collapsed = measure(state, FixedRng(u))
            self.assertEqual(intensities(collapsed), (1, 0) if chosen == 0 else (0, 1))
            self.assertEqual(collapsed[chosen].theta, state[chosen].theta)

    def test_h_zero_total(self):
        with self.assertRaises(ValueError):
            measure((ZERO, ZERO), random.Random(1))
        with self.assertRaises(ValueError):
            measure_graph({}, random.Random(1))
        with self.assertRaises(ValueError):
            probabilities([0, 0])
