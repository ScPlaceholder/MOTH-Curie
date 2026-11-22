"""Build viewer/bench.html from bench_template.html.

Two embedded data blocks:
  __DATA__   the wave-bench frames. Their original generator was not committed, so this script
             carries them forward from the current bench.html verbatim (it refuses if it cannot
             find exactly one `const DATA = ...;` line).
  __QDATA__  the qubit tab: every preset circuit is RUN BY CURIE under curie.trace, and the
             recorded before/after amplitudes of each step are embedded. The page only draws them,
             and its own small browser engine is checked against these steps on load.
Run from the repo root:  python viewer/build_bench.py
"""
import json, math, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from curie import trace as T
from curie.qstate import zeros

HERE = os.path.dirname(os.path.abspath(__file__))
PI = math.pi

PRESETS = [
    dict(key='split', title='Split and rejoin', n=1,
         circuit=[('h', (0,)), ('h', (0,))],
         captions=['Start: the qubit is 0, for certain.',
                   'H splits it into two equal paths. Measure now and it is a coin flip.',
                   'A second H brings the paths back together. The two routes into 1 cancel, so it is 0 again, every time.']),
    dict(key='nudge', title='Split, nudge, rejoin', n=1,
         circuit=[('h', (0,)), ('z', (0,)), ('h', (0,))],
         captions=['Start: 0, for certain.',
                   'H splits it into two equal paths.',
                   'Z turns the 1-path half a circle. Look at the bars: nothing you could measure has changed. Only the hand moved.',
                   'Rejoin. This time the routes into 0 cancel, and it comes out 1 every time. The nudge was invisible until the paths met.']),
    dict(key='bell', title='Entangle two qubits', n=2,
         circuit=[('h', (0,)), ('cnot', (0, 1))],
         captions=['Start: both qubits 0.',
                   'H splits qubit 0. Qubit 1 is untouched.',
                   'CNOT flips qubit 1 only where qubit 0 is 1. Now it is 00 or 11, never 01 or 10. Measure one and you know the other: they are entangled.']),
    dict(key='ghz', title='Entangle three', n=3,
         circuit=[('h', (0,)), ('cnot', (0, 1)), ('cnot', (1, 2))],
         captions=['Start: three qubits, all 0.',
                   'H splits qubit 0.',
                   'CNOT ties qubit 1 to qubit 0.',
                   'CNOT ties qubit 2 to qubit 1. All three now agree: 000 or 111, nothing in between.']),
    dict(key='dj', title='One question, whole answer', n=2,
         circuit=[('h', (0,)), ('h', (1,)), ('oracle_phase', ((0, 1), (0, 1, 1, 0))),
                  ('h', (0,)), ('h', (1,))],
         captions=['Start: 00. A hidden rule answers 0 or 1 for each of the four inputs. Is it the same answer for all of them, or half and half?',
                   'H on qubit 0.',
                   'H on qubit 1. Now all four inputs are in play at once, equally.',
                   'Ask the rule once. Where it answers 1, that path is turned half a circle. The bars do not change; the hands do.',
                   'H on qubit 0.',
                   'H on qubit 1. If the rule were the same everywhere, this would land on 00. It lands on 11, so the rule is half and half, learned from one question instead of three.']),
    dict(key='grover', title='Find the marked one', n=2,
         circuit=[('h', (0,)), ('h', (1,)), ('flip', (3,)),
                  ('h', (0,)), ('h', (1,)), ('x', (0,)), ('x', (1,)), ('mcz', ((0, 1),)),
                  ('x', (0,)), ('x', (1,)), ('h', (0,)), ('h', (1,))],
         captions=['Start: 00. One of the four answers, 11, is marked, and we do not know which.',
                   'H on qubit 0.',
                   'H on qubit 1. All four are equally likely: 25% each.',
                   'The marker turns 11 half a circle. Still 25% each; only its hand flipped.',
                   'Now the amplifier, seven steps that reflect everything about the average. H on qubit 0...',
                   'H on qubit 1...', 'X on qubit 0...', 'X on qubit 1...',
                   'Turn 00 half a circle...', 'X on qubit 0...', 'X on qubit 1...', 'H on qubit 0...',
                   'H on qubit 1. Every other path cancelled; 11 took all of it. 100% in one round.']),
]


def run_presets():
    out = []
    for p in PRESETS:
        assert len(p['captions']) == len(p['circuit']) + 1, p['key']
        with T.tracing() as tr:
            tr.run(p['circuit'], zeros(p['n']))
        d = json.loads(tr.to_json())
        out.append(dict(key=p['key'], title=p['title'], n=d['n'], captions=p['captions'],
                        initial=d['initial'],
                        steps=[dict(op=s['op'], args=s['args'], before=s['before'], after=s['after'])
                               for s in d['steps']],
                        schema=d['schema'], library=d['library_version']))
    return out


def main():
    tpl = open(os.path.join(HERE, 'bench_template.html'), encoding='utf-8').read()
    cur = open(os.path.join(HERE, 'bench.html'), encoding='utf-8').read()
    found = re.findall(r'^const DATA = (.*);$', cur, flags=re.M)
    if len(found) != 1:
        sys.exit('refusing: expected exactly one `const DATA = ...;` line in bench.html, found %d' % len(found))
    if tpl.count('__DATA__') != 1 or tpl.count('__QDATA__') != 1:
        sys.exit('refusing: template must hold exactly one __DATA__ and one __QDATA__')
    q = json.dumps(run_presets(), allow_nan=False, separators=(',', ':'))
    html = tpl.replace('__DATA__', found[0]).replace('__QDATA__', q)
    open(os.path.join(HERE, 'bench.html'), 'w', encoding='utf-8', newline='\n').write(html)
    # the same page ships inside the package, so `curie bench` works after pip install
    open(os.path.join(HERE, '..', 'curie', 'bench.html'), 'w', encoding='utf-8', newline='\n').write(html)
    print('bench.html: %d bytes, %d qubit presets' % (len(html), len(PRESETS)))


if __name__ == '__main__':
    main()
