"""Demonstrate teleportation, Deutsch-Jozsa, and Grover."""
import math
from .programs import (teleport, teleport_circuit, qubit_amplitudes, deutsch_jozsa,
                       grover_probability, run, project, from_amplitudes)


def main():
    a, b = math.cos(.3), math.sin(.3)
    initial = from_amplitudes((a, 0, 0, 0, b, 0, 0, 0))
    before, _ = run(teleport_circuit()[:4], initial)
    for m0 in (0, 1):
        for m1 in (0, 1):
            branch, p0 = project(before, 0, m0)
            _, p1 = project(branch, 1, m1)
            state, _ = teleport(a, b, forced={'m0': m0, 'm1': m1})
            amps = qubit_amplitudes(state, 2)
            print(f'teleport {m0}{m1}: prob {p0*p1:.2f} amplitudes ({amps[0].real:.6f}, {amps[1].real:.6f})')
    for f in (lambda a,b: 0, lambda a,b: a):
        verdict, p = deutsch_jozsa(f, 2)
        print(f'{verdict} p={p:.1f}')
    for k in range(5):
        print(f'Grover k={k}: {grover_probability(3, 0, k):.4f}')


if __name__ == '__main__':
    main()
