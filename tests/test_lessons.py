"""The lessons must run clean, AND their simulation-vs-maths check must be able to fail.

A check that cannot fail teaches nothing: if Curie's engine were wrong and the lesson still printed
"the simulation and the maths agree", it would be teaching the wrong answer with a straight face.
So the second and third tests corrupt the simulation on purpose and require the lesson to stop.
"""
import io
import contextlib
import unittest

from curie import lessons
from curie.qstate import State


class TestLessons(unittest.TestCase):
    def test_all_lessons_run_and_every_step_checks(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = lessons.main([])
        self.assertEqual(rc, 0)
        self.assertEqual(out.getvalue().count("CHECK: the simulation and the maths agree"), 11)

    def test_a_wrong_simulation_is_caught(self):
        real = lessons.apply_1q

        def broken(state, gate, target):          # returns the state UNCHANGED: a gate that does nothing
            return State(state.n, state.amps)

        lessons.apply_1q = broken
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(AssertionError):
                    lessons.interference()
        finally:
            lessons.apply_1q = real

    def test_a_wrong_cnot_is_caught(self):
        real = lessons.cnot
        lessons.cnot = lambda state, c, t: State(state.n, state.amps)   # CNOT that does nothing
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(AssertionError):
                    lessons.entanglement()
        finally:
            lessons.cnot = real

    def test_unknown_lesson_is_refused(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(lessons.main(["nope"]), 2)


if __name__ == "__main__":
    unittest.main()
