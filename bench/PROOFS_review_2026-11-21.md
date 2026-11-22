# Red-team review: the three RELA proofs

**Summary.** H3 holds. H2 and H1 are valid proofs, but each proves a narrower statement than its "What this proves" paragraph claims, and the Overall section repeats the overclaim. The H1 numerical check tests something the theorem says nothing about.

## H3 (identity): RELA's beacon detector is the Rayleigh test

**(1) Steps.** Valid for the batch sum at one fixed ω.
- Step 3 is fine.
- The proof leans on the code doing what the notation section says: `Resonance(1, θ)` must store e^{iθ} with no rescaling or normalisation. That is not shown here, but it is checkable.
- Convention nit: pulsar astronomy usually uses Z₁² = 2|S|²/N. A constant factor changes the threshold, not the ranking, so it doesn't matter as long as thresholds are set consistently.

**(2) Statement vs claim.** There is a mismatch. The claim is about a phasor state "updated per event", which is the exponentially forgetting version. The proof covers the batch, non-forgetting sum. The forgetting version gets one unproved sentence.
- That sentence is true: |S| = |Σ wₖ e^{iωtₖ}| with wₖ = e^{−λ(t_now − tₖ)}.
- Calling it "the windowed Rayleigh statistic" is loose:
  - The /N normalisation no longer fits. It should be Σwₖ² or similar.
  - The null distribution changes, so the thresholds differ.
  - Its prior art is the leaky DFT bin, exponentially weighted periodogram or leaky Goertzel filter. None of these is cited.

**(3) What it proves / does not prove.** "Cannot detect anything the Rayleigh test cannot" only holds if RELA's detector is exactly this score with the same frequency grid, threshold and decision rule. If RELA's detector also uses arg S (phase tracking or drift), combines several ω nonlinearly, or adds any post-processing, the identity does not cover it. Within that scope the paragraph is fine. "Better than existing methods" is refuted because RELA ties Rayleigh, which is an existing method.

**(4) Numerical check.** It supports the identity, at whatever ω and with whichever variant the benchmark ran. The document doesn't say whether that was the batch or forgetting form; it should. Identical detection rates follow from identical scores and add no new evidence. The gap-test numbers are facts about Rayleigh, and the document says so correctly.

**Verdict.** Fine for the batch identity. The forgetting variant, which is the one actually claimed, needs its own two-line proof and its own normalisation.

## H2 (theorem): composition becomes addition only when order does not matter

**(1) Steps.** All valid. This is the trivial fact that an injective homomorphism into a commutative group forces the source to be commutative.

**(2) Statement vs claim.** This is the main defect. The claim says the polar form "removes intermediate calculations". That is a claim about computational cost. The theorem only rules out an exact, injective, everywhere-homomorphic map into a commutative structure. It does not rule out any of these:
- **Non-injective maps**, which keep only the invariant the task needs: determinant phase, global phase, a trace-type quantity.
- **Partial or local additivity.** Angles really do add on commuting sub-structures embedded inside non-commuting circuits. Phase folding and phase-polynomial T-count optimisation (Amy, Maslov, Mosca 2014) merge rotations across CNOTs. That is "composition becomes addition" on a sub-structure, and it is useful.
- **Approximate additivity.** Under BCH, log(eˣeʸ) = X + Y + ½[X, Y] + …; small-angle and Trotter regimes give addition with error you can control.
- **Shortcuts that are not additive at all:** lazy or symbolic composition, tree or parallel-prefix reduction (associativity alone cuts depth), repeated squaring.

**(3) What it proves / does not prove.**
- "No representation can turn non-commuting composition into addition" overclaims. It should read "no *injective homomorphic* representation into a commutative structure". Non-injective and approximate ones exist.
- The Consequence paragraph has the same flaw: "no chart, RELA's or anyone's" needs the same qualifiers.
- The doc underplays its own commuting-case result. There the claim is *true* (angles add); it is just not new (it's the log trick). The doc should say plainly that the claim is true but unoriginal for commuting chains and false for non-commuting ones.
- The eigenbasis remark assumes diagonalisable operators. Commuting but non-diagonalisable operators are not covered. This is minor.

**(4) Numerical check.** It doesn't support the theorem; a theorem needs no numbers. The agreement figures show RELA multiplies matrices correctly. The 44× and 32× slowdowns measure RELA's Python object overhead, not anything about the representation.

**Verdict.** The theorem is fine. The paragraph built on it is stronger than the theorem.

## H1 (theorem): m complex numbers carry no more information than 2m real ones

**(1) Steps.**
- **Step 1** quietly adds "for real data x". If x is complex, the result still holds, but as a real linear sketch of the 2n-dimensional real vector (u, v). The statement should say this.
- **Step 3 is wrong as written.** It gives the inverse as r ↦ B·x + i·C·x, which is written in terms of x and is not a function of r. The correct inverse is (r₁, r₂) ↦ r₁ + i·r₂. The fix is trivial, but it is the first literally incorrect line in the document.
- **Step 5** uses the data-processing inequality informally, for a deterministic function. That is fine.

**(2) Statement vs claim.** This is a serious gap. The claim is about storing relationships as one magnitude and phase per edge, more compactly than conventional records. The theorem assumes a *linear* sketch s = A·x. The proof does not cover:
- **Per-edge storage** that is not a sketch at all. Then the real question is bits per edge against a specific conventional record format.
- **Finite precision.** The theorem counts real numbers, not bits. Quantised phase, for example 4-bit angles, falls outside it.
- **Nonlinear state:** multiplicative updates (`__mul__`), normalisation, phase derived nonlinearly from data, or |·|² fed back into the state.
- **Comparison with non-sketch conventional records**, for example exact adjacency lists.

**(3) What it proves / does not prove.**
- The "no information advantage" sentence needs the qualifier "among linear sketches of real data".
- The "does not prove" paragraph is honest about the ±1 design.
- The Consequence paragraph ("every known lower bound applies") is correct for linear sketches.

**(4) Numerical check.** This is adjacent, not supporting.
- "In squared error, which is what the proof's equivalence is about" is false. The proof is about information, meaning a bijection, not squared error. Equal information says nothing about the squared error of a fixed estimator against a *different* sketch design. The RMS tie comes from variance matching, not from the theorem.
- RMS relative errors of 1.73 and 1.80 mean the error is larger than the signal. Both sketches fail in this regime, so the test can't tell them apart.
- The RMS is reported without a confidence interval. Under heavy tails that is unstable, and the 40-trial reversal shows it.
- The 4/π argument only holds in the sparse regime (at most one collision). The observed ratio is 1.16, not 1.27.
- It also assumes the readout is Re(conj(phase)·bucket). If RELA reads out via |s|², the analysis does not apply.
- The one benchmark that would actually test the theorem is the split (Re, Im) sketch. It would match RELA exactly, and it was not run.

**Verdict.** The proof is valid, apart from the step 3 typo, for linear sketches of real data. That is narrower than the claim, and the paragraph and benchmark wording blur the two.

## Overall section

- "Each of the three claims is beaten by a theorem" overclaims for H2 (only the exact-additive reading is beaten) and for H1 (only the linear-sketch reading is beaten).
- "In every measured case it is slower": no H1 timing was reported. Where timing was reported, the slowdown is implementation overhead, which is irrelevant to the representational claims.

## Still open, beyond the hardware question the document already lists

1. **H3:** detectors that use arg S, combine several frequencies nonlinearly, or rely on the null calibration of the forgetting variant. Whether per-event O(1) streaming over many ω beats existing streaming periodograms on cost.
2. **H2:** approximate (BCH or Trotter) and partial (phase-folding-style) additivity inside non-commuting circuits. Non-injective, task-specific invariants. The ZX-calculus or phase-polynomial optimiser comparison, which has not been run.
3. **H1:** nonlinear or multiplicatively updated RELA state. Bits rather than real-count accounting at finite precision. Per-edge storage against a named conventional record. RELA against the *best* real 2m-row sketch for a defined task, in a regime where relative error is below 1.