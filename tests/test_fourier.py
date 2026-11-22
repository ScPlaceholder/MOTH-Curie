import math
import unittest
from curie.fourier import dft, idft, from_real, tone, spectrum
from curie.rela import Resonance, ZERO, isclose


class FourierTests(unittest.TestCase):
    def assertResonances(self, actual, expected):
        self.assertEqual(len(actual), len(expected))
        for a, b in zip(actual, expected):
            self.assertTrue(isclose(a, b, 1e-9), (a, b))

    def test_a_cosine_one(self):
        values = tone(8, 1)
        self.assertResonances(dft(values), [Resonance(4, 0) if k in (1, 7) else ZERO for k in range(8)])
        for a, b in zip(spectrum(values), [0, 16, 0, 0, 0, 0, 0, 16]):
            self.assertAlmostEqual(a, b, delta=1e-9)

    def test_b_cosine_three(self):
        for k, value in enumerate(spectrum(tone(8, 3))):
            self.assertAlmostEqual(value, 16 if k in (3, 5) else 0, delta=1e-9)

    def test_c_complex_tone(self):
        values = dft(tone(8, 2, complex_=True))
        self.assertResonances(values, [Resonance(8, 0) if k == 2 else ZERO for k in range(8)])
        self.assertAlmostEqual(values[2].intensity, 64, delta=1e-9)

    def test_d_constant(self):
        for value, expected in ((1, Resonance(8, 0)), (-2, Resonance(16, math.pi))):
            values = dft(from_real([value] * 8))
            self.assertResonances(values, [expected] + [ZERO] * 7)
            self.assertAlmostEqual(values[0].intensity, expected.intensity, delta=1e-9)

    def test_e_round_trip(self):
        real = from_real([.5, -1.25, 3, 0, -.75, 2, 1, -3])
        complex_values = [Resonance.from_xy(x, y) for x, y in
                          ((1, 2), (-3, 1), (0, 0), (.5, -1), (2, 3), (-1, -2), (4, 0), (0, 1))]
        for values in (real, complex_values):
            self.assertResonances(idft(dft(values)), values)

    def test_f_parseval(self):
        values = from_real([.5, -1.25, 3, 0, -.75, 2, 1, -3])
        lhs = len(values) * sum(x.intensity for x in values)
        rhs = sum(x.intensity for x in dft(values))
        self.assertTrue(math.isclose(lhs, rhs, rel_tol=1e-9, abs_tol=0))

    def test_g_linearity(self):
        values = from_real([.5, -1.25, 3, 0, -.75, 2, 1, -3])
        for a in (2.5, -3, Resonance(2, math.pi / 3)):
            self.assertResonances(dft([a * x for x in values]), [a * x for x in dft(values)])

    def test_h_empty_and_single(self):
        value = Resonance(2, 1)
        self.assertResonances(dft([value]), [value])
        self.assertEqual(dft([]), [])
        self.assertEqual(idft([]), [])
