"""Run the v1 demonstrations: python -m curie.demo_v1."""
import math
from .rela import ONE, ZERO, interfere_all
from .gates import intensities, interferometer


def main():
    print("Roots of unity:")
    roots = ONE.roots(6)
    grid = [[" " for _ in range(23)] for _ in range(11)]
    for k, root in enumerate(roots):
        degrees = math.degrees(root.theta)
        print(f"  k={k}: r={root.r:.3f}, theta={degrees:.0f} degrees")
        x = round(11 + 10 * math.cos(root.theta))
        y = round(5 - 4 * math.sin(root.theta))
        grid[y][x] = str(k)
    for row in grid:
        print("  " + "".join(row).rstrip())
    result = interfere_all(roots)
    print(f"  interfere_all = {0.0 if result.r < 1e-9 else result.r:.3f}")
    print("Gate interferometer:")
    for label, phi in (("0", 0), ("pi/2", math.pi / 2), ("pi", math.pi)):
        a, b = intensities(interferometer(phi)((ONE, ZERO)))
        print(f"  phi={label}: port 0={a:.3f}, port 1={b:.3f}")


if __name__ == "__main__":
    main()

