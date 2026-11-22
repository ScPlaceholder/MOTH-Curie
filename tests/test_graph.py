import math
import unittest
from curie import (EventGraph, ONE, ZERO, Resonance, isclose, interferometer,
                   observe, ring, total_intensity, rotate)


class GraphTests(unittest.TestCase):
    def test_interferometer(self):
        for phi, d1, d2 in ((0, 1, 0), (math.pi / 2, .5, .5), (math.pi, 0, 1)):
            with self.subTest(phi=phi):
                graph = interferometer(phi)
                graph.run(2)
                for name, expected in (("D1", d1), ("D2", d2)):
                    self.assertAlmostEqual(graph.values[name].intensity, expected, delta=1e-9)
                    self.assertAlmostEqual(observe(graph)[name], expected, delta=1e-9)
                if phi == math.pi:
                    self.assertLess(graph.values["D1"].r, 1e-12)
                self.assertAlmostEqual(total_intensity(graph), 1, delta=1e-9)

    def test_first_step(self):
        graph = interferometer(0)
        graph.step()
        self.assertEqual(graph.values["S"], ZERO)
        self.assertTrue(isclose(graph.values["A"], Resonance(1 / math.sqrt(2), 0)))
        self.assertTrue(isclose(graph.values["B"], Resonance(1 / math.sqrt(2), math.pi / 2)))

    def test_ring(self):
        graph = ring(4)
        for _ in range(4):
            graph.step()
            self.assertAlmostEqual(total_intensity(graph), 1, delta=1e-9)
        self.assertTrue(isclose(graph.values[0], ONE))
        for i in range(1, 4):
            self.assertLess(graph.values[i].r, 1e-12)

    def test_zero_observation(self):
        graph = EventGraph()
        graph.add_node("a")
        graph.add_node("b")
        self.assertEqual(observe(graph), {"a": 0, "b": 0})

    def test_unknown_node(self):
        graph = EventGraph()
        graph.add_node("a")
        for src, dst in (("a", "missing"), ("missing", "a")):
            with self.assertRaises(KeyError):
                graph.add_edge(src, dst, rotate(0))
