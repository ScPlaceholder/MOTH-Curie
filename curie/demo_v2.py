"""Run the v2 demonstrations: python -m curie.demo_v2."""
import math
import random
from .fourier import from_real, spectrum
from .gates import interferometer
from .measure import measure
from .rela import ONE, ZERO


def main():
    print("Spectrum:")
    n = 16
    values = from_real([math.cos(2 * math.pi * 2 * j / n) +
                        0.5 * math.cos(2 * math.pi * 5 * j / n) for j in range(n)])
    powers = spectrum(values)
    for k, power in enumerate(powers):
        print(f"  {k:2d}: {power:6.2f} {'#' * round(40 * power / max(powers))}")
    print("Clicks:")
    rng = random.Random(7)
    for label, phi in (("0", 0), ("pi/2", math.pi / 2), ("pi", math.pi)):
        state = interferometer(phi)((ONE, ZERO))
        clicks = [measure(state, rng)[0] for _ in range(20)]
        print(f"  phi={label}: {''.join(str(k + 1) for k in clicks)} ({clicks.count(0)}, {clicks.count(1)})")


if __name__ == "__main__":
    main()
