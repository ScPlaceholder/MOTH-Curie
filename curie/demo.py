"""Run three demonstrations: python -m curie.demo."""
import argparse
import math
from . import ONE, Resonance, compose, conjugate, interfere, interferometer, ring, rotate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", type=float)
    parser.add_argument("--rounds", type=int, default=4)
    args = parser.parse_args()
    print("ring:")
    graph = ring()
    for i in range(args.rounds):
        graph.step()
        values = " ".join(f"{node}={v.r:.3f}<{v.theta:.3f}" for node, v in graph.values.items())
        print(f"  round {i + 1}: {values}")
    print("mzi:")
    phases = [0, math.pi / 2, math.pi]
    if args.phase is not None:
        phases.append(args.phase)
    for phase in phases:
        graph = interferometer(phase)
        graph.run(2)
        bars = []
        for name in ("D1", "D2"):
            intensity = graph.values[name].intensity
            bar = "#" * round(intensity * 20)
            bars.append(f"{name} [{bar:<20}] {intensity:.3f}")
        print(f"  phi={phase:.3f}: " + "  ".join(bars))
    print("order:")
    reference = Resonance(1, math.pi / 2)
    for label, transform in (("conj-after-rotate", compose(rotate(math.pi / 2), conjugate)),
                             ("rotate-after-conj", compose(conjugate, rotate(math.pi / 2)))):
        value = transform(ONE)
        report = interfere(value, reference)
        print(f"  {label}: {value.r:.3f}<{value.theta:.3f}, "
              f"intensity={report.result.intensity:.3f}, alignment={report.alignment:+.3f}")


if __name__ == "__main__":
    main()
