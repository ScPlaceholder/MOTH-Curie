"""Demonstrate Bell preparation, measurement, and CHSH."""
import random
import sys
from .gates import H
from .qstate import zeros, apply_1q, cnot, measure_all
from .entangle import chsh_value, chsh_sampled


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    rng = random.Random(2024)
    state = zeros(2)
    for title, operation in [('Initial |00>', None), ('After H on q0', lambda s: apply_1q(s, H, 0)),
                             ('After CNOT', lambda s: cnot(s, 0, 1))]:
        if operation:
            state = operation(state)
        print(title)
        for i, amp in enumerate(state.amps):
            print(f"  |{i:02b}>: {amp.r:.6f}∠{amp.theta:.6f}, p={amp.intensity:.6f}")
    print('20 shots:', ' '.join(measure_all(state, rng) for _ in range(20)))
    print(f'CHSH S = {chsh_value(state):.6f} (classical limit 2)')
    print(f'Sampled S = {chsh_sampled(state, 20000, rng):.6f}')


if __name__ == '__main__':
    main()

