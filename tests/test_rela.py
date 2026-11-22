import math
import unittest
from curie import (Resonance, ZERO, ONE, isclose, interfere, interfere_all,
                   rotate, scale, gate, conjugate, compose)


class ResonanceTests(unittest.TestCase):
    def assertResonance(self, actual, expected):
        self.assertTrue(isclose(actual, expected), (actual, expected))

    def test_multiply(self):
        self.assertResonance(Resonance(2, math.pi / 3) * Resonance(3, math.pi / 6),
                             Resonance(6, math.pi / 2))
        self.assertResonance(ONE * -2, Resonance(2, math.pi))
        self.assertResonance(-2 * ONE, Resonance(2, math.pi))

    def test_normalization_and_validation(self):
        self.assertEqual(Resonance(1, -math.pi).theta, math.pi)
        self.assertResonance(Resonance(1, 3 * math.pi), Resonance(1, math.pi))
        with self.assertRaises(ValueError):
            Resonance(-1, 0)
        self.assertEqual(Resonance(0, 2).theta, 0)

    def test_transforms(self):
        self.assertResonance(rotate(math.pi / 2)(ONE), Resonance(1, math.pi / 2))
        x = Resonance(2, math.pi / 3)
        self.assertResonance(conjugate(x), Resonance(2, -math.pi / 3))
        self.assertResonance(x * conjugate(x), Resonance(4, 0))
        self.assertResonance(scale(2)(ONE), Resonance(2, 0))
        self.assertResonance(gate(2, 1)(ONE), Resonance(2, 1))
        with self.assertRaises(ValueError):
            scale(-1)

    def test_intensity(self):
        self.assertEqual(Resonance(3, 1).intensity, 9)

    def test_interference(self):
        cases = [(0, Resonance(2, 0), 1, 2),
                 (math.pi, ZERO, -1, -2),
                 (math.pi / 2, Resonance(math.sqrt(2), math.pi / 4), 0, 0)]
        for angle, result, alignment, gain in cases:
            with self.subTest(angle=angle):
                report = interfere(ONE, Resonance(1, angle))
                self.assertResonance(report.result, result)
                if angle == math.pi:
                    self.assertLess(report.result.r, 1e-12)
                self.assertAlmostEqual(report.alignment, alignment, delta=1e-9)
                self.assertAlmostEqual(report.gain, gain, delta=1e-9)
        self.assertResonance(interfere(Resonance(3, 0), Resonance(1, math.pi)).result,
                             Resonance(2, 0))
        self.assertEqual(interfere(ZERO, ONE).alignment, 1.0)

    def test_interfere_all(self):
        self.assertIs(interfere_all([]), ZERO)
        self.assertLess(interfere_all(Resonance(1, k * math.pi / 2) for k in range(4)).r, 1e-12)

    def test_no_addition(self):
        with self.assertRaises(TypeError):
            ONE + ONE

    def test_order(self):
        reference = Resonance(1, math.pi / 2)
        first = compose(rotate(math.pi / 2), conjugate)(ONE)
        second = compose(conjugate, rotate(math.pi / 2))(ONE)
        self.assertResonance(first, Resonance(1, -math.pi / 2))
        self.assertResonance(second, reference)
        for value, intensity, alignment in ((first, 0, -1), (second, 4, 1)):
            report = interfere(value, reference)
            self.assertAlmostEqual(report.result.intensity, intensity, delta=1e-9)
            self.assertAlmostEqual(report.alignment, alignment, delta=1e-9)
