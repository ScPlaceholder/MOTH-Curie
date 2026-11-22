"""Serializable circuits and small quantum programs."""
import math
import random
from .rela import ZERO
from .gates import H, X, phase
from .qstate import (State, _mask, zeros, basis, from_amplitudes, apply_1q,
                     cnot, cz, swap, ry, measure_qubit)

Op = tuple[str, tuple]


def project(state, q, bit):
    mask = _mask(state, q)
    if bit not in (0, 1):
        raise ValueError('bit must be 0 or 1')
    p = sum(a.intensity for i, a in enumerate(state.amps) if bool(i & mask) == bool(bit))
    if p == 0:
        raise ValueError('impossible measurement outcome')
    return State(state.n, tuple(a * (1 / math.sqrt(p)) if bool(i & mask) == bool(bit)
                                else ZERO for i, a in enumerate(state.amps))), p


def qubit_amplitudes(state, q):
    mask = _mask(state, q)
    pairs = [(state.amps[i], state.amps[i | mask]) for i in range(len(state.amps))
             if not i & mask and (state.amps[i].r > 1e-12 or state.amps[i | mask].r > 1e-12)]
    if len(pairs) != 1:
        raise ValueError('other qubits are not in a definite basis state')
    return pairs[0]


def mcz(state, qubits):
    """Flip selected signs in one O(2**n) pass, not a gate decomposition.

    Hardware n-controlled Z needs O(n) Toffolis and ancillas; this is not modelled.
    """
    masks = [_mask(state, q) for q in qubits]
    if len(set(qubits)) != len(qubits):
        raise ValueError('duplicate qubit')
    mask = sum(masks)
    return State(state.n, tuple(a * -1 if i & mask == mask else a for i, a in enumerate(state.amps)))


def flip(state, index):
    """Flip one sign in an O(2**n) pass, not a gate decomposition."""
    if not isinstance(index, int) or not 0 <= index < len(state.amps):
        raise ValueError('basis index out of range')
    return State(state.n, tuple(a * -1 if i == index else a for i, a in enumerate(state.amps)))


def truth_table(f, n):
    if not isinstance(n, int) or n < 1:
        raise ValueError('n must be positive')
    table = tuple(f(*(int(b) for b in format(i, f'0{n}b'))) for i in range(2**n))
    if any(x not in (0, 1) for x in table):
        raise ValueError('function must be binary')
    return table


def _oracle(state, inputs, table, ancilla=None):
    """Apply an oracle by an O(2**n) permutation or sign pass, not a gate decomposition.

    Hardware n-controlled Z needs O(n) Toffolis and ancillas; this is not modelled.
    """
    masks = [_mask(state, q) for q in inputs]
    if len(set(inputs)) != len(inputs) or len(table) != 2**len(inputs) or any(x not in (0, 1) for x in table):
        raise ValueError('invalid oracle')
    target = _mask(state, ancilla) if ancilla is not None else 0
    if ancilla in inputs:
        raise ValueError('ancilla must differ from inputs')
    amps = [ZERO] * len(state.amps)
    for i, a in enumerate(state.amps):
        key = 0
        for mask in masks:
            key = (key << 1) | bool(i & mask)
        if target:
            amps[i ^ (target if table[key] else 0)] = a
        else:
            amps[i] = a * -1 if table[key] else a
    return State(state.n, tuple(amps))


def run(circuit, state, rng=None, forced=None):
    bits = {}
    rng = rng if rng is not None else random.Random()
    forced = forced if forced is not None else {}
    def execute(op, state):
        name, args = op
        if name in ('h', 'x', 'z', 'ry', 'phase'):
            q = args[0]
            gate = {'h': lambda: H, 'x': lambda: X, 'z': lambda: phase(math.pi),
                    'ry': lambda: ry(args[1]), 'phase': lambda: phase(args[1])}[name]()
            return apply_1q(state, gate, q)
        if name in ('cnot', 'cz', 'swap'):
            return {'cnot': cnot, 'cz': cz, 'swap': swap}[name](state, *args)
        if name == 'mcz':
            return mcz(state, *args)
        if name == 'flip':
            return flip(state, *args)
        if name == 'oracle_xor':
            inputs, ancilla, table = args
            return _oracle(state, inputs, table, ancilla)
        if name == 'oracle_phase':
            return _oracle(state, *args)
        if name == 'measure':
            q, key = args
            if key in forced:
                bit = forced[key]
                state, _ = project(state, q, bit)
            else:
                bit, state = measure_qubit(state, q, rng)
            bits[key] = bit
            return state
        if name == 'if':
            key, inner = args
            return execute(inner, state) if bits[key] == 1 else state
        raise ValueError('unknown operation: ' + str(name))
    for op in circuit:
        state = execute(op, state)
    return state, bits


def teleport_circuit():
    return [('h', (1,)), ('cnot', (1, 2)), ('cnot', (0, 1)), ('h', (0,)),
            ('measure', (0, 'm0')), ('measure', (1, 'm1')),
            ('if', ('m1', ('x', (2,)))), ('if', ('m0', ('z', (2,))))]


def teleport(a, b, rng=None, forced=None):
    state = from_amplitudes((a, 0, 0, 0, b, 0, 0, 0))
    state, bits = run(teleport_circuit(), state, rng, forced)
    return state, (bits['m0'], bits['m1'])


def dj_circuit(table, n, oracle='xor'):
    table = tuple(table)
    if n < 1 or len(table) != 2**n or any(x not in (0, 1) for x in table):
        raise ValueError('invalid truth table')
    if sum(table) not in (0, len(table) // 2, len(table)):
        raise ValueError('function must be constant or balanced')
    inputs = tuple(range(n))
    if oracle == 'xor':
        op = ('oracle_xor', (inputs, n, table))
        qs = range(n + 1)
    elif oracle == 'phase':
        op = ('oracle_phase', (inputs, table))
        qs = inputs
    else:
        raise ValueError('unknown oracle')
    return [('h', (q,)) for q in qs] + [op] + [('h', (q,)) for q in inputs]


def deutsch_jozsa(f, n, oracle='xor'):
    table = truth_table(f, n)
    circuit = dj_circuit(table, n, oracle)
    state = basis(n + 1, '0' * n + '1') if oracle == 'xor' else zeros(n)
    state, _ = run(circuit, state)
    p = sum(a.intensity for i, a in enumerate(state.amps) if i >> (1 if oracle == 'xor' else 0) == 0)
    return ('constant' if p > 0.5 else 'balanced'), p


def optimal_iterations(n):
    if not isinstance(n, int) or n < 1:
        raise ValueError('n must be positive')
    return max(0, round(math.pi / (4 * math.asin(1 / math.sqrt(2**n))) - 0.5))


def grover_circuit(n, marked, k):
    if not isinstance(n, int) or n < 1 or not isinstance(marked, int) or not 0 <= marked < 2**n:
        raise ValueError('invalid marked item or qubit count')
    if not isinstance(k, int) or k < 0:
        raise ValueError('k must be nonnegative')
    h = [('h', (q,)) for q in range(n)]
    x = [('x', (q,)) for q in range(n)]
    # Diffusion is -(2|s><s|-I); the global minus does not change probabilities.
    return h + ([('flip', (marked,))] + h + x + [('mcz', (tuple(range(n)),))] + x + h) * k


def grover_probability(n, marked, k):
    state, _ = run(grover_circuit(n, marked, k), zeros(n))
    return state.amps[marked].intensity
