import unittest

from tests import TestParserTimes


if __name__ == '__main__':
    ts = unittest.TestSuite()
    ts.addTest(TestParserTimes())

    unittest.main(verbosity=2)
