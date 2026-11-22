"""Independent complex-number replay of recorded unitary circuits."""
import json
import math
import cmath


class VerifyResult:
    def __init__(self, ok, step, reason):
        self.ok, self.step, self.reason = ok, step, reason


def _values(pairs):
    return [r * cmath.exp(1j * t) for r, t in pairs]


def _apply(s, n, op, args):
    size = len(s)
    mask = lambda q: 1 << (n - 1 - q)
    out = s[:]
    if op in ('h', 'x', 'z', 'ry', 'phase'):
        q = mask(args[0])
        if op == 'h':
            c = 1 / math.sqrt(2); matrix = (c, c, c, -c)
        elif op == 'x':
            matrix = (0, 1, 1, 0)
        elif op == 'z':
            matrix = (1, 0, 0, -1)
        elif op == 'phase':
            matrix = (1, 0, 0, cmath.exp(1j * args[1]))
        else:
            c, v = math.cos(args[1] / 2), math.sin(args[1] / 2)
            matrix = (c, -v, v, c)
        a, b, c, d = matrix
        for i in range(size):
            if not i & q:
                out[i], out[i | q] = a*s[i] + b*s[i | q], c*s[i] + d*s[i | q]
    elif op in ('cnot', 'cz', 'swap'):
        a, b = map(mask, args)
        for i in range(size):
            if op == 'cnot':
                out[i ^ (b if i & a else 0)] = s[i]
            elif op == 'cz':
                out[i] = -s[i] if i & a and i & b else s[i]
            else:
                out[i ^ (a | b) if bool(i & a) != bool(i & b) else i] = s[i]
    elif op in ('flip', 'mcz', 'oracle_phase', 'oracle_xor'):
        for i in range(size):
            if op == 'flip':
                out[i] = -s[i] if i == args[0] else s[i]
            elif op == 'mcz':
                out[i] = -s[i] if all(i & mask(q) for q in args[0]) else s[i]
            else:
                inputs, table = args[0], args[-1]
                key = 0
                for q in inputs:
                    key = (key << 1) | bool(i & mask(q))
                if op == 'oracle_phase':
                    out[i] = -s[i] if table[key] else s[i]
                else:
                    out[i ^ (mask(args[1]) if table[key] else 0)] = s[i]
    else:
        raise NotImplementedError
    return out


def verify(trace_dict, tol=1e-9):
    def fail(step, reason):
        return VerifyResult(False, step, reason)
    try:
        t = trace_dict
        if t['schema'] != 'curie.trace/1' or t['thresholds'] != {'eps': 1e-9}:
            return fail(None, 'schema mismatch')
        n, circuit, steps = t['n'], t['circuit'], t['steps']
        if not isinstance(n, int) or n < 1 or len(t['initial']) != 2**n:
            return fail(None, 'schema mismatch')
        if len(steps) != len(circuit):
            return fail(None, 'length mismatch')
        for i, (step, op) in enumerate(zip(steps, circuit)):
            if [step['op'], step['args']] != op:
                return fail(i, 'step does not match circuit')
        s = _values(t['initial'])
        def close(pairs, expected):
            actual = _values(pairs)
            return len(actual) == len(expected) and all(abs(a-b) <= tol for a, b in zip(actual, expected))
        for i, step in enumerate(steps):
            if not close(step['before'], s):
                return fail(i, 'before-state does not chain')
            try:
                s = _apply(s, n, step['op'], step['args'])
            except NotImplementedError:
                return fail(i, 'unsupported op')
            if not close(step['after'], s):
                return fail(i, 'after-state mismatch')
        return VerifyResult(True, None, 'VERIFIED')
    except (KeyError, TypeError, ValueError, IndexError, OverflowError):
        return fail(None, 'schema mismatch')


def verify_json(text):
    try:
        return verify(json.loads(text))
    except (ValueError, TypeError):
        return VerifyResult(False, None, 'schema mismatch')

