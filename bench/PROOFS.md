# RELA's three claims: the mathematics, written out

These are the arguments behind an independent red-team review that rejected these claims on paper, written
as proofs a reader can check line by line. The numbers that back each one come from
`bench/rela_vs_claims.py` (results: `bench/rela_vs_claims_results_2026-11-21.txt`).

Every proof states exactly what it proves and what it does not. A proof that is read as covering more than it
covers is a wrong proof.

Notation: a RELA `Resonance` with radius r and angle θ is the complex number z = r·e^{iθ}. This is not an
analogy. `rela.interfere(a, b)` returns `Resonance.from_xy(a.real + b.real, a.imag + b.imag)`
(`curie/rela.py`), so interference is complex addition exactly, and `Resonance.__mul__` multiplies radii and
adds angles, which is complex multiplication exactly.

---

## H3 (identity). RELA's beacon detector is the Rayleigh test

**Claim tested.** A phasor state updated per event detects periodic beacons in irregular event times better
than existing methods.

**Statement.** For event times t₁ … t_N and angular frequency ω, the RELA state
S(ω) = interfere_all(Resonance(1, −ω t₁), …, Resonance(1, −ω t_N)) equals Σₖ e^{−iω tₖ}, and the RELA score
|S(ω)|²/N equals the Rayleigh statistic Z(ω) = |Σₖ e^{iω tₖ}|²/N.

**Proof.**
1. `Resonance(1, −ω tₖ)` is e^{−iω tₖ}, by the notation above.
2. `interfere` is complex addition, so interfering N values left to right gives their sum:
   S(ω) = Σₖ e^{−iω tₖ}.
3. Complex conjugation does not change magnitude, and conj(Σₖ e^{−iω tₖ}) = Σₖ e^{iω tₖ}.
   So |S(ω)| = |Σₖ e^{iω tₖ}|.
4. Hence |S(ω)|²/N = |Σₖ e^{iω tₖ}|²/N = Z(ω), the Rayleigh statistic (used in pulsar astronomy to test
   whether arrival phases are uniformly spread). ∎

The exponentially forgetting variant S ← S·e^{−(λ+iω)Δt} + 1 is the same sum with each term weighted by
wₖ = e^{−λ(t_now − tₖ)}. That is a leaky DFT bin / exponentially weighted periodogram, not exactly the Rayleigh
statistic: its normalisation is Σwₖ² rather than N, and its null distribution differs (the red-team review). **The benchmark
used the batch (non-forgetting) form**, so the identity above is what was measured. Pulsar astronomy often writes
Z₁² = 2|S|²/N; the factor changes thresholds, not rankings.

**Numerical check.** Over every stream in the benchmark, |RELA score − Rayleigh score| ≤ 7.6 × 10⁻¹⁴
(floating-point rounding), and both detected beacons at identical rates in every condition.

**What this proves.** RELA's detector cannot detect anything the Rayleigh test cannot, because it computes
the same number. **What it does not prove.** That the Rayleigh test is the best detector. The benchmark
shows it is not, against jittered beacons with their own channel (a gap test scored 1.00 against 0.33), and
that it is good against clock-locked beacons hidden in mixed traffic (0.90 against 0.05). Those are facts
about the Rayleigh test, which was known before RELA.

---

## H2 (theorem). "Composition becomes addition" only works when order does not matter

**Claim tested.** RELA's polar form, where combining rotations means adding angles, removes intermediate
calculations when composing chains of transformations.

**Statement.** Let G be a set of transformations closed under composition. If there is a one-to-one map
L from G into a set where composition becomes addition, that is L(g∘h) = L(g) + L(h) with + commutative,
then every pair in G commutes: g∘h = h∘g.

**Proof.**
1. Take any g, h in G.
2. L(g∘h) = L(g) + L(h), by the property of L.
3. L(g) + L(h) = L(h) + L(g), because addition is commutative.
4. L(h) + L(g) = L(h∘g), by the property of L again.
5. So L(g∘h) = L(h∘g). L is one-to-one, so g∘h = h∘g. ∎

**Consequence.** Most transformations of interest do not commute. Two quantum gates generally give a different
result in the opposite order, and so do 3-D rotations. For those there is no chart, RELA's or anyone's, in
which composing them is just adding numbers. You have to multiply matrices (or quaternions), which is what
RELA's `Gate.__matmul__` does too.

For the part that does commute (operations sharing an eigenbasis), the conventional method already does
the same thing: Uⁿ = V·diag(λ₁ⁿ, λ₂ⁿ)·V⁻¹, and λⁿ in polar form is rⁿ at angle nθ, an angle multiplication.
That is the log-domain trick (logarithms, 1614).

**Numerical check.** On 2000-gate chains, RELA's product agrees with plain complex matrices to 1.4 × 10⁻¹⁴,
and is 44× slower on non-commuting chains. On commuting (diagonal) chains it agrees with simply summing the
angles in ordinary floats to 9 × 10⁻¹², and is 32× slower than doing that.

**What this proves.** No **exact, one-to-one, everywhere-homomorphic** representation can turn non-commuting
composition into addition. It does not rule out non-injective maps that keep only the invariant a task needs,
partial additivity on commuting sub-structures inside non-commuting circuits (phase folding, Amy-Maslov-Mosca 2014,
already does this usefully), approximate additivity (BCH, small angles), or non-additive shortcuts such as
repeated squaring. On commuting chains the claim is **true but not new** (the log-domain trick); on non-commuting
chains, in its exact form, it is false. The measured slowdowns are Curie's Python object overhead, not a property of
the representation. **What it does
not prove.** That RELA could not find some other algebraic shortcut, one that is not "turn it into addition",
which a good optimiser misses. The review names ZX-calculus as the mature phase-based optimiser that this would have
to beat. That comparison has not been run.

---

## H1 (theorem). m complex numbers carry no more information than 2m real ones

**Claim tested.** Storing relationships as RELA amplitudes (a magnitude and phase per edge) represents a system
more compactly than conventional records, without losing information a task needs.

**Statement.** Let a RELA sketch store m complex values computed linearly from the data x (counts, events):
s = A·x, with A an m-row complex matrix. Then there is a real linear sketch with 2m rows that determines
exactly the same information: any quantity computable from s is computable from it, and vice versa.

**Proof.**
1. Write A = B + iC, with B and C real m-row matrices. For real data x, s = A·x = B·x + i·C·x.
2. Define the real sketch r = (B·x, C·x), stacking the two real m-vectors into one 2m-vector.
3. The map s ↦ r (split into real and imaginary parts) is one-to-one, with inverse (r₁, r₂) ↦ r₁ + i·r₂.
   *(Corrected 2026-11-21 after the red-team review: the first version wrote the inverse in terms of x,
   which is not a function of r.)*
4. So any function f of s is the function f∘(inverse) of r, and any function of r is a function of s.
   They carry identical information. ∎
5. A readout such as |s|² (RELA's Born-rule step) is a fixed function applied after the sketch. By the
   data-processing inequality, applying a function can lose information and never gain it.

**Consequence.** Every known lower bound for real linear sketches with 2m rows applies to RELA's m-amplitude
sketch. The best RELA can do is tie a 2m-row real sketch; phase is, in information terms, exactly a second
real number.

**Numerical check.** The benchmark compared m = 64 RELA buckets with 128 real buckets of a different, common
design (random ±1 signs), over 400 trials. In squared error they tie (this follows from variance matching between the two designs, not from the theorem,
which is about information): RMS relative error 1.73 (RELA) against 1.80 (real). In absolute error RELA is slightly worse,
0.495 against 0.427 (2.5 standard errors), which is expected rather than surprising. A complex collision adds
error c·cos(Δθ), whose mean absolute size is (2/π)·c, at twice the collision rate of the 2m-bucket sketch, so
its expected absolute error is about 4/π ≈ 1.27 times the ±1 sketch's at equal variance. (A 40-trial run
first read RMS 2.07 against 1.37. That was noise from heavy-tailed collisions, and it is recorded here
because it was reported before it was corrected.)

**What this proves.** Among **linear sketches of real data**, RELA has no information advantage over a real sketch
of twice its length. It does not cover per-edge storage that is not a sketch, finite-precision (bit) accounting,
or nonlinear or multiplicatively updated RELA state (the red-team review). Those remain open. **What it does
not prove.** That RELA's particular sketch performs as well as any particular real one: the theorem matches it
with *some* real 2m-row sketch (one with cosine and sine weights), not with the ±1 design. That is why the
benchmark matters alongside the proof.

---

## Overall

Each claim, **in its exact form**, is beaten by a theorem or an identity: H3 (batch form) is the Rayleigh test; H2 in
its exact-additive reading is impossible for non-commuting operations and unoriginal for commuting ones; H1 among
linear sketches of real data has no information advantage. RELA computed correctly in every case, and nowhere did it
do something a conventional method could not. (Its measured slowness is implementation overhead, and says nothing
about the mathematics.)

Narrower or different readings that these proofs do **not** cover, listed by the red-team review and still open: H3 with
phase tracking (arg S), nonlinear combination across frequencies, or the forgetting variant's own calibration; H2 as
partial or approximate additivity inside non-commuting circuits (the ZX-calculus / phase-polynomial comparison has not
been run); H1 for nonlinear state, bit-level accounting, per-edge storage against a named record format, and RELA
against the best real 2m-row sketch in a regime where relative error is below 1.

Open, and not covered here: whether RELA's cost table (rotation free, addition by interference, readout by
|·|²) is the natural cost table of real photonic or analog hardware, and if so whether deriving algorithms in
RELA finds anything the existing optical-circuit literature (Reck 1994, Clements 2016) has not.
