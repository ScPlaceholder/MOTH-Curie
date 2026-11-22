"""RELA against its three claims, measured locally. Run from the repo root:

    python bench/rela_vs_claims.py            # full run (about a minute)
    python bench/rela_vs_claims.py --quick    # smaller, for a smoke test

An independent red-team paper review (2026-11-21) rejected H1-H3. This file measures them. Every RELA-side computation uses Curie's own arithmetic (curie.rela.Resonance and
interfere, curie.gates.Gate), never a faster stand-in, because the claim under test is about RELA.

PREDICTIONS, written before the first run and printed at the top of every run so they cannot move:
  H3-P1  RELA's phasor statistic equals the Rayleigh statistic for every stream (|difference| < 1e-9).
         They are the same mathematics; if this fails, the identity in the review is wrong.
  H3-P2  So RELA and Rayleigh detect beacons at identical rates, at the same false-alarm rate.
  H3-P3  Against clock-locked beacons (0% jitter) in HEAVY background, the phasor detectors beat the
         gap test (the review's one stated niche). With 50% jitter, the gap test beats both.
  H3-P4  RELA costs far more per event than the gap test (about F times, F = frequencies scanned).
  H2-P1  RELA's Gate product agrees with a plain complex 2x2 product to < 1e-9.
  H2-P2  On non-commuting chains RELA is SLOWER than plain complex (addition is the hard operation).
  H2-P3  On commuting (diagonal) chains RELA's angle-addition shortcut is real, and it is exactly the
         conventional log-domain method: summing angles in plain floats gives the same answer.
  H1-P1  A sketch of m RELA (complex) buckets recovers counts no better than 2m real buckets: the
         errors tie, within noise.
"""
import cmath
import math
import random
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from curie.rela import Resonance, ZERO, interfere          # noqa: E402
from curie.gates import Gate                                  # noqa: E402

QUICK = "--quick" in sys.argv
TWO_PI = 2 * math.pi


def _arg(name, default):
    """--name VALUE from argv, else default. Added for the larger follow-up runs (J, 2026-11-21 20:31:
    'confirm the claims with actual math and test the system for real')."""
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return default


ONLY = _arg("--only", "")                      # "h1", "h2" or "h3"; empty = all three
H1_TRIALS = int(_arg("--h1-trials", "0"))      # 0 = the default (10 quick / 40 full)


# ---------------------------------------------------------------------------------------------
# H3: beacon detection in an irregular event stream
# ---------------------------------------------------------------------------------------------
T = 7200.0                 # window, seconds (2 h)
P = 300.0                  # beacon period, seconds (5 min)
BEACON_RATE = 1.0 / P
FREQS = [k / T for k in range(int(T / 900), int(T / 60) + 1)]   # periods 60 s .. 900 s, step 1/T


def make_stream(rng, jitter, bg_multiple, beacon=True):
    """Event times in [0, T). Beacon: renewal process, gap = P * (1 - U(0, jitter)) (Cobalt Strike
    style). Background: Poisson at bg_multiple x the beacon rate."""
    ev = []
    if beacon:
        t = rng.uniform(0, P)
        while t < T:
            ev.append(t)
            t += P * (1 - rng.uniform(0, jitter)) if jitter else P
    lam = bg_multiple * BEACON_RATE
    if lam > 0:
        t = rng.expovariate(lam)
        while t < T:
            ev.append(t)
            t += rng.expovariate(lam)
    ev.sort()
    return ev


def rela_score(ev):
    """Max over the frequency bank of |S|^2/N, with S accumulated by RELA interference only."""
    n = len(ev)
    best = 0.0
    for f in FREQS:
        w = TWO_PI * f
        s = ZERO
        for t in ev:
            s = interfere(s, Resonance(1.0, -w * t)).result
        best = max(best, s.intensity / n)
    return best


def rayleigh_score(ev):
    """The same statistic with plain complex numbers (the conventional Rayleigh test)."""
    n = len(ev)
    best = 0.0
    for f in FREQS:
        w = TWO_PI * f
        s = sum(cmath.exp(-1j * w * t) for t in ev)
        best = max(best, abs(s) ** 2 / n)
    return best


def gap_score(ev):
    """Interval regularity, RITA-style: 1 - MAD/median of inter-arrival gaps. Near 1 = regular."""
    gaps = [b - a for a, b in zip(ev, ev[1:])]
    if len(gaps) < 4:
        return 0.0
    med = statistics.median(gaps)
    mad = statistics.median(abs(g - med) for g in gaps)
    return 1.0 - (mad / med if med > 0 else 1.0)


DETECTORS = [("RELA phasor", rela_score), ("Rayleigh", rayleigh_score), ("gap MAD", gap_score)]


def h3():
    rng = random.Random(20261121)
    n_streams = 12 if QUICK else 40
    jitters = [0.0, 0.25, 0.5]
    # "solo" = the per-connection case interval tests are built for: the beacon alone, against benign
    # Poisson traffic at the beacon's rate. Without it the gap test is only ever judged off its home
    # ground (background mixed into the beacon's own stream breaks every interval).
    backgrounds = [("solo", 0.0), ("light", 1.0), ("heavy", 5.0)]
    print("\n=== H3: beacon detection ===")
    print("window %.0f s, beacon period %.0f s, %d frequencies scanned, %d streams per cell, threshold at 5%% false alarms"
          % (T, P, len(FREQS), n_streams))
    max_identity_gap = 0.0
    cost = {name: [0.0, 0] for name, _ in DETECTORS}   # seconds, events
    rows = []
    for bg_name, bg in backgrounds:
        nulls = [make_stream(rng, 0.0, bg if bg else 1.0, beacon=False) for _ in range(n_streams)]
        thresholds = {}
        null_scores = {}
        for name, fn in DETECTORS:
            sc = []
            for ev in nulls:
                t0 = time.perf_counter(); sc.append(fn(ev)); cost[name][0] += time.perf_counter() - t0
                cost[name][1] += len(ev)
            null_scores[name] = sc
            thresholds[name] = sorted(sc)[int(0.95 * len(sc)) - 1] if len(sc) > 1 else sc[0]
        for a, b in zip(null_scores["RELA phasor"], null_scores["Rayleigh"]):
            max_identity_gap = max(max_identity_gap, abs(a - b))
        for j in jitters:
            streams = [make_stream(rng, j, bg) for _ in range(n_streams)]
            det = {}
            scores = {}
            for name, fn in DETECTORS:
                sc = []
                for ev in streams:
                    t0 = time.perf_counter(); sc.append(fn(ev)); cost[name][0] += time.perf_counter() - t0
                    cost[name][1] += len(ev)
                scores[name] = sc
                det[name] = sum(s > thresholds[name] for s in sc) / len(sc)
            for a, b in zip(scores["RELA phasor"], scores["Rayleigh"]):
                max_identity_gap = max(max_identity_gap, abs(a - b))
            rows.append((bg_name, j, det))
    print("\n  background  jitter   RELA phasor   Rayleigh   gap MAD    (detection rate at 5% false alarms)")
    for bg_name, j, det in rows:
        print("  %-10s  %4.0f%%     %6.2f       %6.2f     %6.2f" % (
            bg_name, 100 * j, det["RELA phasor"], det["Rayleigh"], det["gap MAD"]))
    print("\n  cost per event (microseconds):")
    for name, _ in DETECTORS:
        s, n = cost[name]
        print("    %-12s %10.2f" % (name, 1e6 * s / n))
    print("  max |RELA - Rayleigh| over every stream: %.3e" % max_identity_gap)
    return rows, cost, max_identity_gap


# ---------------------------------------------------------------------------------------------
# H2: composing transformations
# ---------------------------------------------------------------------------------------------
def rand_unitary(rng):
    """A random 2x2 unitary as plain complex rows."""
    a, b, c = (rng.uniform(0, TWO_PI) for _ in range(3))
    th = rng.uniform(0, math.pi / 2)
    u00 = cmath.exp(1j * a) * math.cos(th)
    u01 = cmath.exp(1j * b) * math.sin(th)
    u10 = -cmath.exp(1j * (c - b)) * math.sin(th)
    u11 = cmath.exp(1j * (c - a)) * math.cos(th)
    return ((u00, u01), (u10, u11))


def to_gate(m):
    R = lambda z: Resonance(abs(z), cmath.phase(z))     # noqa: E731
    return Gate.from_rows(R(m[0][0]), R(m[0][1]), R(m[1][0]), R(m[1][1]))


def cmul(x, y):
    return ((x[0][0] * y[0][0] + x[0][1] * y[1][0], x[0][0] * y[0][1] + x[0][1] * y[1][1]),
            (x[1][0] * y[0][0] + x[1][1] * y[1][0], x[1][0] * y[0][1] + x[1][1] * y[1][1]))


def h2():
    rng = random.Random(7)
    n = 400 if QUICK else 2000
    print("\n=== H2: composition of %d gates ===" % n)
    mats = [rand_unitary(rng) for _ in range(n)]
    gates = [to_gate(m) for m in mats]
    t0 = time.perf_counter()
    gp = gates[0]
    for g in gates[1:]:
        gp = gp @ g
    t_rela = time.perf_counter() - t0
    t0 = time.perf_counter()
    cp = mats[0]
    for m in mats[1:]:
        cp = cmul(cp, m)
    t_cplx = time.perf_counter() - t0
    agree = max(abs(complex(gp.m[i][j].real, gp.m[i][j].imag) - cp[i][j]) for i in range(2) for j in range(2))
    print("  non-commuting chain: RELA %.4f s, plain complex %.4f s (RELA %.1fx), max disagreement %.2e"
          % (t_rela, t_cplx, t_rela / t_cplx, agree))
    # Commuting: diagonal phase gates. RELA's polar shortcut is angle addition; so is the log domain.
    angles = [(rng.uniform(0, TWO_PI), rng.uniform(0, TWO_PI)) for _ in range(n)]
    t0 = time.perf_counter()
    d0, d1 = Resonance(1, 0), Resonance(1, 0)
    for a, b in angles:
        d0, d1 = d0 * Resonance(1, a), d1 * Resonance(1, b)
    t_rela_d = time.perf_counter() - t0
    t0 = time.perf_counter()
    s0 = sum(a for a, _ in angles); s1 = sum(b for _, b in angles)
    t_log = time.perf_counter() - t0
    t0 = time.perf_counter()
    c0, c1 = 1 + 0j, 1 + 0j
    for a, b in angles:
        c0 *= cmath.exp(1j * a); c1 *= cmath.exp(1j * b)
    t_cd = time.perf_counter() - t0
    same = max(abs(cmath.exp(1j * d0.theta) - cmath.exp(1j * s0)), abs(cmath.exp(1j * d1.theta) - cmath.exp(1j * s1)))
    print("  commuting chain:     RELA polar %.4f s, plain log-domain (sum angles) %.5f s, plain complex %.4f s"
          % (t_rela_d, t_log, t_cd))
    print("                       RELA vs log-domain answer differ by %.2e" % same)
    return t_rela, t_cplx, agree, t_rela_d, t_log, t_cd, same


# ---------------------------------------------------------------------------------------------
# H1: compression, m complex buckets vs 2m real buckets
# ---------------------------------------------------------------------------------------------
def h1():
    rng = random.Random(11)
    U, m, trials = 2000, 64, (H1_TRIALS or (10 if QUICK else 40))
    print("\n=== H1: count recovery, %d items, %d RELA buckets vs %d real buckets, %d trials ===" % (U, m, 2 * m, trials))
    err_rela, err_real = [], []
    for _ in range(trials):
        counts = [int(1000 / (i + 1) ** 1.1) for i in range(U)]   # Zipf-like
        hb = [rng.randrange(m) for _ in range(U)]
        ph = [rng.uniform(0, TWO_PI) for _ in range(U)]
        hr = [rng.randrange(2 * m) for _ in range(U)]
        sg = [rng.choice((-1, 1)) for _ in range(U)]
        rb = [ZERO] * m
        for i, c in enumerate(counts):
            if c:
                rb[hb[i]] = interfere(rb[hb[i]], Resonance(c, ph[i])).result
        realb = [0.0] * (2 * m)
        for i, c in enumerate(counts):
            realb[hr[i]] += sg[i] * c
        top = range(20)
        for i in top:
            est = (rb[hb[i]] * Resonance(1, -ph[i])).real      # RELA estimate: rotate back, take real part
            err_rela.append(abs(est - counts[i]) / max(counts[i], 1))
            err_real.append(abs(sg[i] * realb[hr[i]] - counts[i]) / max(counts[i], 1))
    mr, mx = statistics.mean(err_rela), statistics.mean(err_real)
    sd = statistics.pstdev([a - b for a, b in zip(err_rela, err_real)]) / math.sqrt(len(err_rela))
    # The theory's tie is in SQUARED error (variance: complex collisions weigh cos^2 = 1/2 each, at twice
    # the collision rate). Mean absolute error is a different yardstick; report both, not the kinder one.
    rr = math.sqrt(statistics.mean(e * e for e in err_rela))
    rx = math.sqrt(statistics.mean(e * e for e in err_real))
    print("  mean relative error on the top-20 items: RELA (m complex) %.4f, real (2m reals) %.4f, difference %.4f +/- %.4f (1 s.e.)"
          % (mr, mx, mr - mx, sd))
    print("  RMS relative error:                       RELA (m complex) %.4f, real (2m reals) %.4f" % (rr, rx))
    return mr, mx, sd, rr, rx


if __name__ == "__main__":
    print(__doc__.split("PREDICTIONS")[1].split('"""')[0].rstrip().replace(", written before", "PREDICTIONS, written before", 1))
    t0 = time.perf_counter()
    if ONLY in ("", "h3"):
        h3r = h3()
    if ONLY in ("", "h2"):
        h2r = h2()
    if ONLY in ("", "h1"):
        h1r = h1()
    print("\n== rela_vs_claims COMPLETE in %.1f s ==" % (time.perf_counter() - t0))
