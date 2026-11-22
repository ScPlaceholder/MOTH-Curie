import math
import random
import unittest
from curie.rela import interfere
from curie.gates import H, X
from curie.qstate import zeros, apply_1q
from curie.entangle import bell, ghz, is_product_state, chsh_value, chsh_sampled


class EntangleTests(unittest.TestCase):
    def test_product(self):
        state = bell('phi+')
        a, b, c, d = state.amps
        self.assertAlmostEqual(interfere(a*d, (b*c)*-1).result.r, .5, delta=1e-12)
        self.assertFalse(is_product_state(state))
        self.assertTrue(is_product_state(zeros(2)))
        self.assertTrue(is_product_state(apply_1q(apply_1q(zeros(2), H, 0), X, 1)))
        with self.assertRaises(ValueError):
            is_product_state(zeros(3))

    def test_chsh(self):
        for state, expected in ((bell('phi+'), 2*math.sqrt(2)), (bell('psi-'), -2*math.sqrt(2)),
                                (bell('phi-'), 0), (zeros(2), math.sqrt(2))):
            self.assertAlmostEqual(chsh_value(state), expected, delta=1e-9)
        value = chsh_sampled(bell('phi+'), 20000, random.Random(2024))
        print('q1 sampled CHSH seed 2024:', value)
        self.assertLess(abs(value - 2*math.sqrt(2)), .1)

    def test_ghz(self):
        p = ghz(3).probabilities()
        self.assertAlmostEqual(p[0], .5, delta=1e-12)
        self.assertAlmostEqual(p[7], .5, delta=1e-12)
        self.assertEqual(p[1:7], [0.0] * 6)
