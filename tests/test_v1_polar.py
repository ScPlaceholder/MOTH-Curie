import math
import unittest
from curie.rela import Resonance, ZERO, ONE, isclose, interfere_all


class PolarTests(unittest.TestCase):
    def assertR(self, a, b):
        self.assertTrue(isclose(a, b, 1e-9), (a, b))

    def test_p1_division(self):
        self.assertR(Resonance(6, 1) / Resonance(2, .4), Resonance(3, .6))
        self.assertR(Resonance(2, .5) / 2, Resonance(1, .5))
        self.assertR(2 / Resonance(2, .5), Resonance(1, -.5))
        self.assertIs(ONE.__truediv__(object()), NotImplemented)
        self.assertIs(ONE.__rtruediv__(object()), NotImplemented)

    def test_p2_inverse(self):
        z = Resonance(2, .5)
        self.assertR(z.inverse() * z, ONE)

    def test_p3_zero(self):
        for op in (lambda: ZERO.inverse(), lambda: ONE / ZERO,
                   lambda: ONE / 0, lambda: ZERO ** -1):
            with self.assertRaises(ZeroDivisionError):
                op()

    def test_p4_powers(self):
        z = Resonance(2, .3)
        self.assertR(z ** 3, Resonance(8, .9))
        self.assertEqual(z ** 0, ONE)
        self.assertEqual(ZERO ** 0, ONE)
        self.assertR(z ** -2, Resonance(.25, -.6))
        self.assertIs(z.__pow__(1.5), NotImplemented)

    def test_p5_normalization(self):
        z = Resonance(1, 3) ** 2
        self.assertGreater(z.theta, -math.pi)
        self.assertLessEqual(z.theta, math.pi)
        self.assertAlmostEqual(z.theta, 6 - 2 * math.pi, delta=1e-9)

    def test_p6_roots(self):
        for z in (Resonance(2, .7), Resonance(5, -2.5), Resonance(1, math.pi)):
            for n in range(1, 8):
                roots = z.roots(n)
                self.assertEqual(len(roots), n)
                for root in roots:
                    self.assertR(root ** n, z)

    def test_p7_unity_roots(self):
        for n in range(1, 13):
            for k, root in enumerate(ONE.roots(n)):
                self.assertR(root, Resonance(1, 2 * math.pi * k / n))

    def test_p8_sum(self):
        for n in range(2, 13):
            self.assertR(interfere_all(ONE.roots(n)), ZERO)

    def test_p9_square_roots(self):
        for root, expected in zip(Resonance(4, 0).roots(2),
                                  (Resonance(2, 0), Resonance(2, math.pi))):
            self.assertR(root, expected)
        self.assertEqual(ZERO.roots(3), [ZERO] * 3)

    def test_p10_principal(self):
        self.assertR(Resonance(1, math.pi).principal_root(2), Resonance(1, math.pi / 2))

    def test_p11_invalid(self):
        for n in (0, -1, 1.5):
            with self.assertRaises(ValueError):
                ONE.roots(n)
