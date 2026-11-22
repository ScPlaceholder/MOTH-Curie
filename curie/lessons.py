"""Guided lessons: every step shown twice, as the simulation and as the maths.

    python -m curie.lessons                 # all three
    python -m curie.lessons interference    # or: entanglement, grover

For each step a lesson prints:
  SIMULATION  what Curie's engine produced (each amplitude as size and angle, and its probability)
  MATHS       the same step worked by hand: which amplitudes combine, with which numbers, and what they
              add up to. This column is computed INDEPENDENTLY, in plain Python complex numbers, not by
              Curie's RELA engine.
  CHECK       whether the two agree. If they ever disagree the lesson stops with an error rather than
              teaching something wrong. So every run is also a test of Curie.

Qubit 0 is the most significant bit: in a 2-qubit state, |10> is amplitude index 2.
"""
import cmath
import math
import sys

from .gates import H, X, phase
from .qstate import State, zeros, apply_1q, cnot
from .programs import mcz
from .entangle import is_product_state

TOL = 1e-9


# ------------------------------------------------------------------------------------------------
# Formatting
# ------------------------------------------------------------------------------------------------
def c(z):
    """Complex number from a RELA Resonance, or pass a complex through."""
    return complex(z.real, z.imag) if not isinstance(z, complex) else z


def fmt(z):
    """A complex number the way a student would write it: 0.707, -0.5, 0.707i, 0.5-0.5i."""
    z = c(z)
    re = 0.0 if abs(z.real) < 5e-10 else z.real
    im = 0.0 if abs(z.imag) < 5e-10 else z.imag
    if im == 0:
        return "%.3f" % re
    if re == 0:
        return "%.3fi" % im
    return "%.3f%+.3fi" % (re, im)


def label(i, n):
    return "|" + format(i, "0%db" % n) + ">"


def show_state(state, title):
    print("   SIMULATION (%s)" % title)
    for i, a in enumerate(state.amps):
        if a.r > TOL:
            print("     %s  amplitude %-14s = size %.3f at angle %+7.1f deg   probability %.3f"
                  % (label(i, state.n), fmt(a), a.r, math.degrees(a.theta), a.intensity))
    zeroes = [label(i, state.n) for i, a in enumerate(state.amps) if a.r <= TOL]
    if zeroes:
        print("     (amplitude 0 for: %s)" % ", ".join(zeroes))


def check(before, after_curie, expected):
    """expected: list of complex amplitudes computed by hand. Raise if Curie disagrees."""
    worst = max(abs(c(a) - e) for a, e in zip(after_curie.amps, expected))
    if worst > TOL:
        raise AssertionError("Curie and the hand maths disagree by %.2e. Stopping rather than teach this." % worst)
    print("   CHECK: the simulation and the maths agree (largest difference %.1e)" % worst)


def gate_matrix(g):
    return [[c(g.m[0][0]), c(g.m[0][1])], [c(g.m[1][0]), c(g.m[1][1])]]


def step_1q(state, g, name, target, why):
    """Apply a one-qubit gate, show the matrix, every pair of amplitudes it mixes, and the check."""
    n = state.n
    m = gate_matrix(g)
    print("\n -- Apply %s to qubit %d. %s" % (name, target, why))
    print("   MATHS: %s is the matrix  [ %s  %s ]" % (name, fmt(m[0][0]), fmt(m[0][1])))
    print("                         [ %s  %s ]" % (fmt(m[1][0]), fmt(m[1][1])))
    print("   It mixes each pair of amplitudes that differ only in qubit %d:" % target)
    mask = 1 << (n - 1 - target)
    amps = [c(a) for a in state.amps]
    expected = list(amps)
    for i in range(len(amps)):
        if i & mask:
            continue
        j = i | mask
        a, b = amps[i], amps[j]
        if abs(a) < TOL and abs(b) < TOL:
            continue
        na = m[0][0] * a + m[0][1] * b
        nb = m[1][0] * a + m[1][1] * b
        expected[i], expected[j] = na, nb
        print("     new %s = (%s)(%s) + (%s)(%s) = %s" % (label(i, n), fmt(m[0][0]), fmt(a), fmt(m[0][1]), fmt(b), fmt(na)))
        print("     new %s = (%s)(%s) + (%s)(%s) = %s" % (label(j, n), fmt(m[1][0]), fmt(a), fmt(m[1][1]), fmt(b), fmt(nb)))
        for k, before_k, after_k in ((i, (a, b), na), (j, (a, b), nb)):
            t1 = m[0][0] * a if k == i else m[1][0] * a
            t2 = m[0][1] * b if k == i else m[1][1] * b
            if abs(t1) > TOL and abs(t2) > TOL:
                if abs(after_k) < TOL:
                    print("       -> %s: the two contributions CANCEL (destructive interference)" % label(k, n))
                elif abs(abs(after_k) - (abs(t1) + abs(t2))) < TOL:
                    print("       -> %s: the two contributions ADD UP (constructive interference)" % label(k, n))
    after = apply_1q(state, g, target)
    show_state(after, "after %s" % name)
    check(state, after, expected)
    return after


# ------------------------------------------------------------------------------------------------
# Lesson 1: interference
# ------------------------------------------------------------------------------------------------
def interference():
    print("\n=================== LESSON 1: INTERFERENCE ===================")
    print("One qubit. A Hadamard (H) splits it into two equal paths. A second H recombines them.")
    print("Whether the paths reinforce or cancel depends on their relative phase.\n")
    s = zeros(1)
    show_state(s, "start")
    s = step_1q(s, H, "H", 0, "Split |0> into an equal mix of |0> and |1>.")
    s = step_1q(s, H, "H", 0, "Recombine. Watch |1> cancel and |0> come back.")
    print("\n   So H then H does nothing at all: the two routes to |1> arrive with opposite signs and cancel.")
    print("\n Now do it again, but nudge one path's phase by 180 degrees in the middle.")
    s = zeros(1)
    s = step_1q(s, H, "H", 0, "Split again.")
    s = step_1q(s, phase(math.pi), "Z (phase 180 deg)", 0, "Turn the |1> path around: multiply its amplitude by -1.")
    s = step_1q(s, H, "H", 0, "Recombine. This time it is |0> that cancels.")
    print("\n   The same two gates, one phase flip between them, and the answer moves from |0> to |1>.")
    print("   That is the whole trick behind every quantum algorithm: arrange phases so the wrong answers cancel.")


# ------------------------------------------------------------------------------------------------
# Lesson 2: entanglement
# ------------------------------------------------------------------------------------------------
def entanglement():
    print("\n=================== LESSON 2: ENTANGLEMENT ===================")
    print("Two qubits. H on qubit 0, then CNOT (flip qubit 1 if qubit 0 is 1). The result can no longer")
    print("be described one qubit at a time.\n")
    s = zeros(2)
    show_state(s, "start")
    s = step_1q(s, H, "H", 0, "Put qubit 0 in an equal mix; qubit 1 is still |0>.")
    print("   Is this a product state (describable qubit by qubit)? %s" % ("yes" if is_product_state(s) else "no"))
    print("\n -- Apply CNOT with control qubit 0 and target qubit 1.")
    print("   MATHS: CNOT swaps the amplitudes of |10> and |11> (control is 1) and leaves |00>, |01> alone:")
    amps = [c(a) for a in s.amps]
    expected = [amps[0], amps[1], amps[3], amps[2]]
    print("     new |00> = old |00> = %s,   new |01> = old |01> = %s" % (fmt(amps[0]), fmt(amps[1])))
    print("     new |10> = old |11> = %s,   new |11> = old |10> = %s" % (fmt(amps[3]), fmt(amps[2])))
    after = cnot(s, 0, 1)
    show_state(after, "after CNOT")
    check(s, after, expected)
    s = after
    print("   Is this a product state? %s" % ("yes" if is_product_state(s) else "no"))
    print("\n   Why not: a product state's amplitudes factor as (a|0> + b|1>)(c|0> + d|1>), so")
    print("   amp(00) x amp(11) must equal amp(01) x amp(10). Here:")
    a = [c(x) for x in s.amps]
    print("     amp(00) x amp(11) = %s x %s = %s" % (fmt(a[0]), fmt(a[3]), fmt(a[0] * a[3])))
    print("     amp(01) x amp(10) = %s x %s = %s" % (fmt(a[1]), fmt(a[2]), fmt(a[1] * a[2])))
    print("   They differ, so no pair of single-qubit states can produce this. The qubits are entangled:")
    print("   measure one and you know the other, with probability 1, every time.")


# ------------------------------------------------------------------------------------------------
# Lesson 3: Grover search
# ------------------------------------------------------------------------------------------------
def grover():
    print("\n=================== LESSON 3: GROVER SEARCH ===================")
    print("Four items (two qubits). One is marked: |11>. A classical search checks them one at a time.")
    print("Grover finds it in ONE step, by making the marked item's amplitude grow and the others cancel.\n")
    s = zeros(2)
    s = step_1q(s, H, "H", 0, "Start spreading: qubit 0 into an equal mix.")
    s = step_1q(s, H, "H", 1, "Now qubit 1 too: all four items have amplitude 0.5.")
    print("\n -- ORACLE: flip the sign of the marked item |11>.")
    print("   MATHS: multiply amp(11) by -1; nothing else changes. Probabilities are unchanged too,")
    print("   because (-0.5)^2 = 0.5^2. The mark is invisible to measurement and lives only in the phase.")
    amps = [c(a) for a in s.amps]
    expected = amps[:3] + [-amps[3]]
    after = mcz(s, [0, 1])
    show_state(after, "after the oracle")
    check(s, after, expected)
    s = after
    print("\n -- DIFFUSION: reflect every amplitude about the average. This is what turns phase into probability.")
    amps = [c(a) for a in s.amps]
    mean = sum(amps) / len(amps)
    expected = [2 * mean - a for a in amps]
    print("   MATHS: average amplitude = (%s) / 4 = %s" % (" + ".join(fmt(a) for a in amps), fmt(mean)))
    for i, (a, e) in enumerate(zip(amps, expected)):
        print("     new %s = 2 x average - old = 2 x %s - (%s) = %s" % (label(i, 2), fmt(mean), fmt(a), fmt(e)))
    print("   (In gates: H, X on both qubits, flip the sign of |11>, X, H. Curie runs that sequence below.)")
    d = s
    for q in (0, 1):
        d = apply_1q(d, H, q)
    for q in (0, 1):
        d = apply_1q(d, X, q)
    d = mcz(d, [0, 1])
    for q in (0, 1):
        d = apply_1q(d, X, q)
    for q in (0, 1):
        d = apply_1q(d, H, q)
    show_state(d, "after diffusion")
    # The gate sequence implements I - 2|s><s|, which is the textbook "2 x average - old" times -1.
    # That -1 multiplies EVERY amplitude: a global phase, invisible to any measurement. The first run of
    # this lesson stopped here (Curie -1.000, hand maths +1.000), which is exactly what the check is for.
    # So the lesson says so and checks against the hand maths including that -1.
    print("   NOTE: Curie shows -1.000 where the hand maths said +1.000. That is not an error. The gate")
    print("   sequence computes (old - 2 x average), the same reflection multiplied by -1 everywhere. A sign")
    print("   applied to EVERY amplitude is a global phase: it changes no probability and no measurement can")
    print("   detect it. Checking against the hand maths with that -1 included:")
    check(s, d, [-e for e in expected])
    print("\n   The marked item now has probability 1 and the other three cancelled to 0. One query, found.")
    print("   (With more items it takes about (pi/4) x sqrt(N) rounds, not one; four items is the case where")
    print("   a single round lands exactly.)")


LESSONS = {"interference": interference, "entanglement": entanglement, "grover": grover}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    names = argv or list(LESSONS)
    for name in names:
        if name not in LESSONS:
            print("unknown lesson %r; choose from: %s" % (name, ", ".join(LESSONS)))
            return 2
        LESSONS[name]()
    print("\nAll steps checked: the simulation and the hand maths agreed every time.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
