# Red-team paper review: RELA H4 (photonic cost model), 2026-11-21

Source: an independent red-team paper review, 2026-11-21. Written analysis; no code.

# Review: is RELA the native cost model of photonic hardware? Verdict: KILL

## (1) A claim that can be false

**H4.** Start from an N×N linear-optical task: a target unitary U, or a target intensity map x ↦ |Ux|². There is a task family where an algorithm derived in RELA uses fewer resources than the best published construction. That construction may come from Reck 1994, Clements 2016, butterfly or FFT meshes, or numerical circuit synthesis. The resource is one of these, named in advance:
- (a) number of two-mode elements (MZIs or beam splitters);
- (b) number of programmable phase shifters;
- (c) optical depth, which is a proxy for worst-path loss;
- (d) number of detectors.

"Fewer" means either asymptotically fewer, or provably minimal where the literature gives only an upper bound.

**"Not already known"** means the construction is neither in that literature nor a direct instance of Givens, Householder or butterfly factorization of the target matrix.

**H4 is false if** the literature already has matching lower and upper bounds for the general case and for the obvious structured tasks, **or** if RELA's cost table does not describe the hardware. Both hold.

## (2) Does the cost table match the hardware? Mostly the reverse.

| RELA says | Hardware reality |
|---|---|
| **Rotation (phase) is free** | Phase shifters are the expensive part. They are the only programmable element. Thermo-optic heaters cost about 10–30 mW each, take roughly 100 µm of chip area, suffer thermal crosstalk, and reconfigure in µs–ms. Power, area and calibration cost scale with the phase-shifter count. A *fixed* phase is free only if it is etched in, and then it is not a variable. |
| **Scaling is native** | Amplitude below 1 means attenuation, which is loss: an MZI used as an attenuator throws power away. Amplitude above 1 needs an amplifier, which adds noise. Scaling is not free. |
| **Addition happens by interference** | A beam splitter is a 2×2 *unitary*. It outputs (a+b)/√2 and (a−b)/√2 together. Getting "a+b" alone means throwing away the difference port, which costs 3 dB. Combining N inputs into one output costs a factor of N in power, because unitarity forces it. So addition is not an operation with a price you can lower. It is passive and cheap in elements, but it always comes paired with a subtraction you are forced to discard. |
| **Readout is \|.\|²** | This part matches: photodiodes are square-law. But it destroys phase. Recovering phase needs homodyne detection with a local oscillator, which adds detectors and phase locking. Shot noise and ADCs dominate the energy budget, not the optics. |
| **Not in the model at all** | Loss that compounds with depth (about 0.1–0.5 dB per MZI), fabrication error, and the lack of any optical nonlinearity. Without nonlinearity you get data × fixed weight, never data × data. The only data × data term is the single quadratic form the detector computes. |

What does match — a unitary map on amplitudes followed by square-law detection — is just the standard linear-optics model. It has been formalised for decades: unitary circuits over U(2) gates, Aaronson–Arkhipov for multi-photon inputs, and programmable linear maps for coherent light. RELA adds no axiom beyond it, and it puts the costs on the wrong operations.

## (3) The baselines are already tight

**General U(N): element count.** U(N) has real dimension N². Each U(2) block factors as D·T: a diagonal phase part D with 2 parameters times an MZI-type part T with 2 parameters. Conjugating by diagonals keeps a block on the same pair of modes, so every diagonal factor can be pushed to one end. A product of k blocks therefore covers a set of dimension at most N + 2k. Covering U(N) needs N + 2k ≥ N², so **k ≥ N(N−1)/2**. Reck and Clements meet this exactly (N(N−1)/2 MZIs plus N output phases, N² parameters). The phase-shifter count of N² is also exactly minimal.

**General U(N): depth.** One layer holds at most ⌊N/2⌋ elements, so depth is at least about N−1. With nearest-neighbour coupling, the light-cone argument also gives N−1 (mode 1 must reach mode N). Clements achieves depth N and balances loss across paths. That is optimal up to one layer.

**Compaction and robustness:** this design space is already heavily mined.
- Miller 2013: self-configuring meshes.
- Clements 2016: balanced-loss rectangular mesh.
- Fldzhyan–Saygin–Kulik 2020, Bell–Walmsley 2021: fewer elements or fixed beam-splitter layers.
- Hamerly et al. 2022: error-tolerant 3-MZI cells.
- Labroille 2014: multi-plane light conversion.
- Shen 2017: SVD with two meshes plus attenuators for non-unitary maps.

**DFT and Walsh–Hadamard.**
- In free space, a lens performs the DFT with zero discrete elements.
- On chip, butterfly meshes use (N/2)·log₂N beam splitters at depth log₂N (Barak–Ben-Aryeh 2007; Crespi et al. 2016; Fang et al. 2019 for ONNs).
- Depth ≥ log₂N is forced: each output depends on every input, and fan-in doubles per layer.
- Element count Ω(N log N) for unitary 2×2-gate circuits: Ailon 2013, matrix-entropy argument. I'm confident about the bound but not certain of the exact title and venue.
- So the DFT is Θ(N log N) elements at Θ(log N) depth. Hadamard follows the same butterfly argument.

**Grover-type search with classical waves:** already done in N modes (Cerf–Adami–Kwiat 1998; Bhattacharya et al. PRL 2002, Fourier optics). It needs one mode per item, i.e. resources exponential in qubit count. No advantage is available there.

## (4) Cheapest kill test: done on paper

The dimension count in (3) shows that **the general case is closed and optimal**: N(N−1)/2 MZIs, N² phase shifters, depth about N, all matched by Reck and Clements.

For structured tasks, the DFT and Hadamard sit at Θ(N log N) with log N depth, and both bounds are proven. What is still genuinely open is exact minimal counts or depths for small N, or under fixed connectivity. Those are combinatorial circuit-synthesis problems, attacked with SAT or numerical search. RELA brings no tool for them: a "native RELA derivation" of a mesh *is* a Givens or butterfly factorization of the matrix, written in polar form.

**Mis-pricing check.** Suppose an algorithm is optimal under RELA's table (rotation free, addition expensive). It would spend phase shifters lavishly to save beam splitters. That is the wrong trade on real chips, where phase shifters cost power and area and beam splitters are passive. So even a RELA-optimal design would not be hardware-optimal.

## (5) Verdict: KILL

1. **The model is not new.** The part of RELA's cost model that matches the hardware (unitary on amplitudes plus |.|² readout) is the standard linear-optics model.
2. **The costs are wrong.** The part that is specific to RELA (rotation free, addition priced, scaling native) does not describe the hardware: phase shifters are the costly element, beam-splitter "addition" is forced to be unitary and lossy, and scaling is loss.
3. **Nothing is left to win.** Under any correct resource measure, the general case is tight by dimension counting, and the canonical structured case (DFT) is tight by Ailon plus the light-cone argument.

No benchmark is warranted.

## (6) Bottom line for RELA as a computational research programme

**None.** H1, H2, H3 and now H4 are dead. Each reduces to a known object: real/complex dimension counting, log-domain arithmetic, the Rayleigh test, and Givens or butterfly factorization of unitaries. At most RELA is a teaching notation for phasor arithmetic. It is not a source of algorithms.