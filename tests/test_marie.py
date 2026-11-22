import unittest

from curie.marie import tribute


class TestMarie(unittest.TestCase):
    def test_tribute_names_both_prizes(self):
        text = tribute()
        self.assertIn('1903', text)
        self.assertIn('1911', text)
        self.assertIn('polonium', text)


if __name__ == '__main__':
    unittest.main()
