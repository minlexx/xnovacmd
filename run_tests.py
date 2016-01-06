import unittest

from tests import TestParser


if __name__ == '__main__':
    ts = unittest.TestSuite()
    ts.addTest(TestParser())

    unittest.main(verbosity=2)
