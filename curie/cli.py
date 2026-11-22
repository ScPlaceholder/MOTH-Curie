"""The `curie` command.

    curie lessons [interference|entanglement|grover]   step-by-step lessons, maths beside simulation
    curie bench [--print-path]                         open the wave bench page in your browser
    curie demo [q1|q2|q3]                              the tours: entanglement, programs, the microscope
    curie version
"""
import argparse
import os
import sys
import webbrowser
from pathlib import Path

__version__ = '0.1.0'

DEMOS = {'q1': 'entanglement', 'q2': 'programs (teleportation, Deutsch-Jozsa, Grover)', 'q3': 'the microscope'}


def bench_path() -> Path:
    """The wave bench page shipped inside the package (built by viewer/build_bench.py)."""
    return Path(__file__).resolve().parent / 'bench.html'


def _cmd_lessons(args):
    from . import lessons
    return lessons.main(args.names)


def _cmd_bench(args):
    page = bench_path()
    if not page.is_file():
        print('bench page not found at %s' % page, file=sys.stderr)
        return 1
    if args.print_path:
        print(page)
        return 0
    print('opening %s' % page)
    if not webbrowser.open(page.as_uri()):
        print('could not open a browser; open that file yourself', file=sys.stderr)
        return 1
    return 0


def _cmd_demo(args):
    import importlib
    importlib.import_module('curie.demo_' + args.which).main()
    return 0


def _cmd_marie(args):
    from .marie import TEXT
    print(TEXT)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog='curie', description='Curie, a quantum-computation microscope. A MOTH project.')
    sub = p.add_subparsers(dest='cmd')
    lp = sub.add_parser('lessons', help='step-by-step lessons: the simulation and the hand maths, checked against each other')
    lp.add_argument('names', nargs='*', help='interference, entanglement or grover (default: all three)')
    lp.set_defaults(func=_cmd_lessons)
    bp = sub.add_parser('bench', help='open the wave bench page in your browser')
    bp.add_argument('--print-path', action='store_true', help='print where the page is instead of opening it')
    bp.set_defaults(func=_cmd_bench)
    dp = sub.add_parser('demo', help='a guided tour: ' + '; '.join('%s = %s' % kv for kv in DEMOS.items()))
    dp.add_argument('which', nargs='?', default='q1', choices=sorted(DEMOS))
    dp.set_defaults(func=_cmd_demo)
    sub.add_parser('version', help='print the version').set_defaults(func=lambda a: print('curie', __version__) or 0)
    sub.add_parser('marie', help=argparse.SUPPRESS).set_defaults(func=_cmd_marie)
    args = p.parse_args(argv)
    if not getattr(args, 'func', None):
        p.print_help()
        return 0
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
