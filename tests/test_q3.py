import copy
import json
import math
import unittest
from curie import rela
from curie.diff import diff, equal_up_to_phase
from curie.programs import grover_circuit, run
from curie.qstate import zeros
from curie.trace import tracing, classify, explain
from curie.verify import verify


class MicroscopeTests(unittest.TestCase):
    def trace(self):
        with tracing() as t:
            state = t.run(grover_circuit(2, 3, 1), zeros(2))
        return json.loads(t.to_json()), state

    def test_classes_and_hook(self):
        for r, angle, expected in [(1, 0, 'constructive'), (1, math.pi, 'cancel'),
                                   (1, math.pi/2, 'partial'), (.5, math.pi, 'destructive'),
                                   (0, 0, 'trivial')]:
            a, b = rela.Resonance(1, 0), rela.Resonance(r, angle)
            self.assertEqual(classify(a, b, rela.interfere(a, b)), expected)
        with self.assertRaises(RuntimeError):
            with tracing():
                with tracing():
                    pass
        self.assertIsNone(rela._TRACE_HOOK)

    def test_trace_and_tamper(self):
        data, state = self.trace()
        self.assertAlmostEqual(state.probabilities()[3], 1)
        self.assertTrue(verify(data).ok)
        self.assertIn('Step 0 (h): TV = 0.5', explain(data))
        self.assertIn('Step 1 (h): TV = 0.5', explain(data))
        self.assertIn('Step 2 (flip): TV = 0', explain(data))
        d = copy.deepcopy(data); d['steps'][2]['after'][0][0] += .1
        self.assertEqual((verify(d).step, verify(d).reason), (2, 'after-state mismatch'))
        d = copy.deepcopy(data); d['steps'][1]['args'] = [0]; d['circuit'][1][1] = [0]
        self.assertEqual(verify(d).step, 1)
        d = copy.deepcopy(data); del d['steps'][1]; del d['circuit'][1]
        self.assertEqual((verify(d).step, verify(d).reason), (1, 'before-state does not chain'))
        d = copy.deepcopy(data); del d['steps'][1]
        self.assertEqual(verify(d).reason, 'length mismatch')
        d = copy.deepcopy(data)
        for a in d['initial']: a[1] += math.pi
        self.assertEqual(verify(d).step, 0)
        d = copy.deepcopy(data); d['steps'][1]['after'][0][1] += 2*math.pi
        self.assertTrue(verify(d).ok)

    def test_diff(self):
        initial, _ = run([('h', (0,)), ('h', (1,))], zeros(2))
        cz = [('cz', (0, 1))]
        good = [('h', (1,)), ('cnot', (0, 1)), ('h', (1,))]
        bad = good[:-1] + [('h', (0,))]
        self.assertTrue(diff(cz, good, initial, [('end', 1, 3)]).equivalent)
        self.assertFalse(diff(cz, [], initial).equivalent)
        self.assertTrue(diff(good, bad, initial).equivalent)
        self.assertEqual(diff(good, bad, zeros(2)).where, 2)
        result = diff([('h', (0,))], [('h', (0,)), ('ry', (0, 2*math.pi))], initial)
        self.assertTrue(result.equivalent)
        self.assertAlmostEqual(abs(result.phase), math.pi)
        self.assertTrue(equal_up_to_phase([1, 1], [1j, 1j])[0])


if __name__ == '__main__': unittest.main()
