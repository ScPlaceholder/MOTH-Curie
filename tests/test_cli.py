import contextlib
import io
import unittest
from pathlib import Path

from curie import cli


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        rc = cli.main(argv)
    return rc, out.getvalue()


class TestCli(unittest.TestCase):
    def test_version(self):
        rc, out = run(['version'])
        self.assertEqual(rc, 0)
        self.assertIn(cli.__version__, out)

    def test_lesson_runs_and_checks(self):
        rc, out = run(['lessons', 'interference'])
        self.assertEqual(rc, 0)
        self.assertIn('agreed every time', out)

    def test_unknown_lesson_is_refused(self):
        rc, _ = run(['lessons', 'no-such-lesson'])
        self.assertEqual(rc, 2)

    def test_bench_page_ships_with_the_package(self):
        rc, out = run(['bench', '--print-path'])
        self.assertEqual(rc, 0)
        self.assertTrue(Path(out.strip()).is_file())

    def test_packaged_page_matches_the_viewer_page(self):
        viewer = Path(__file__).resolve().parent.parent / 'viewer' / 'bench.html'
        if not viewer.is_file():
            self.skipTest('not running from the repository')
        self.assertEqual(cli.bench_path().read_bytes(), viewer.read_bytes(),
                         'curie/bench.html is stale: run python viewer/build_bench.py')


if __name__ == '__main__':
    unittest.main()
