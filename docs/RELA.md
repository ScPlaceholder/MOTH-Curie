# RELA: the mathematics Curie is written in, and what we tested

This is the research behind Curie's arithmetic, moved here from the README so the README stays short.
File paths below are relative to the repository root.

Curie is written in **RELA** (Relational Event and Amplitude Mathematics), the owner's framework, built from
events, relations, amplitudes and interference rather than from quantities. Every amplitude is a RELA
`Resonance`: a magnitude and a phase (`curie/rela.py`). Multiplying (scaling and rotating) is native;
adding is the hard operation, done only through `interfere()`.

That choice is about readability and the questions it lets you ask. It is not a speed claim. In pure
Python, RELA's polar arithmetic is measured at roughly 29x slower than Python's built-in complex numbers for
multiplication and 108x slower for addition. At 12 qubits that does not matter.

**What is and is not established.** Curie computes quantum circuits *correctly* in RELA: that is checked
(below). Whether RELA does anything *better* than standard mathematics was tested, and the answer is no.
Five ideas were put to the test, each with a precise claim, the strongest conventional baseline, and a kill
test written before any code:

| idea | result |
|---|---|
| polar form makes homomorphic encryption cheaper | failed on paper |
| relational compression (m resonances hold more than 2m reals) | failed: a resonance is exactly two reals, proved and measured |
| transformation composition becomes simple addition | failed: impossible for non-commuting operations, and known (the log domain) for commuting ones |
| per-event phasor anomaly detection | it is the Rayleigh test, proved identical and confirmed by measurement |
| RELA as the cost model of photonic hardware | failed: phase shifters are the costly part, and the known circuit constructions are already optimal |

The proofs are in `bench/PROOFS.md` (reviewed, with the review alongside it), the photonic review in
`bench/RELA_H4_photonic_review_2026-11-21.md`, and the measurements in
`bench/rela_vs_claims.py`. RELA is a clear way to *write* complex arithmetic,
which is why Curie uses it, and nothing more. Nothing in this repository claims that RELA beats a
conventional method.
