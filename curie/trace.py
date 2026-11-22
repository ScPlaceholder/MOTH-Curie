"""Recording and explaining unitary circuit runs."""
import json
from contextlib import contextmanager
from . import rela, programs

TRACE_SCHEMA = 'curie.trace/1'
LIBRARY_VERSION = 'curie-wave3'


def classify(a, b, report, eps=1e-9):
    if a.r <= eps or b.r <= eps:
        return 'trivial'
    if report.result.r <= eps:
        return 'cancel'
    if report.alignment < -eps:
        return 'destructive'
    if report.alignment >= 1 - eps:
        return 'constructive'
    return 'partial'


def polar(a):
    return [a.r, a.theta]


def encode(value, op):
    if isinstance(value, (tuple, list)):
        return [encode(v, op) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ValueError('non-serialisable argument for op ' + op)


class Trace:
    def __init__(self):
        self.steps = []
        self.loose_events = []
        self.circuit = []
        self.initial = None
        self.n = None
        self._events = None

    def _hook(self, a, b, report):
        event = dict(a=polar(a), b=polar(b), result=polar(report.result),
                     alignment=report.alignment, gain=report.gain,
                     **{'class': classify(a, b, report)})
        (self.loose_events if self._events is None else self._events).append(event)

    def run(self, circuit, state):
        if self.initial is not None:
            raise ValueError('a trace records one run')
        circuit = list(circuit)
        for name, args in circuit:
            if name in ('measure', 'if'):
                raise NotImplementedError('measurement and conditional operations cannot be traced')
            encode(args, name)
        self.n = state.n
        self.initial = [polar(a) for a in state.amps]
        for i, (name, args) in enumerate(circuit):
            encoded = encode(args, name)
            self.circuit.append([name, encoded])
            step = dict(index=i, op=name, args=encoded,
                        before=[polar(a) for a in state.amps], events=[])
            self._events = step['events']
            try:
                state, _ = programs.run([(name, args)], state)
            finally:
                self._events = None
            step['after'] = [polar(a) for a in state.amps]
            self.steps.append(step)
        return state

    def to_json(self):
        return json.dumps(dict(schema=TRACE_SCHEMA, library_version=LIBRARY_VERSION,
                               n=self.n, thresholds={'eps': 1e-9}, circuit=self.circuit,
                               initial=self.initial, steps=self.steps,
                               loose_events=self.loose_events), allow_nan=False)


@contextmanager
def tracing():
    if rela._TRACE_HOOK is not None:
        raise RuntimeError('nested tracing is not supported')
    trace = Trace()
    rela._TRACE_HOOK = trace._hook
    try:
        yield trace
    finally:
        rela._TRACE_HOOK = None


def explain(trace_dict):
    names = ('trivial', 'cancel', 'destructive', 'constructive', 'partial')
    counts = {name: 0 for name in names}
    worst = None
    lines = []
    for step in trace_dict['steps']:
        for event in step['events']:
            counts[event['class']] += 1
            if event['class'] != 'trivial' and (worst is None or event['gain'] < worst[0]):
                worst = (event['gain'], step['index'], step['op'])
    for event in trace_dict['loose_events']:
        counts[event['class']] += 1
    lines.append('Events: ' + ', '.join(f'{k}={counts[k]}' for k in names))
    lines.append(f'Most destructive: step {worst[1]} ({worst[2]}), gain {worst[0]:.6g}'
                 if worst else 'Most destructive: none')
    for step in trace_dict['steps']:
        tv = sum(abs(a[0] ** 2 - b[0] ** 2) for a, b in zip(step['before'], step['after'])) / 2
        lines.append(f"Step {step['index']} ({step['op']}): TV = {tv:.6g}")
    final = trace_dict['steps'][-1]['after'] if trace_dict['steps'] else trace_dict['initial']
    index = max(range(len(final)), key=lambda i: final[i][0])
    lines.append(f"Most likely: basis state {index} (|{index:0{trace_dict['n']}b}>), p = {final[index][0] ** 2:.1f}")
    return '\n'.join(lines)

