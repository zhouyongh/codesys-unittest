# test_test_ops_contract.py - L2 contract checks for the runner decisions.
# These cover the pure gates that run_tests() uses; the full CODESYS path is
# covered by the live SmAxis3 smoke (L4).
# Run: python -m unittest discover -s tests -v

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ut_parse import (
    MAX_CASES,
    allow_start,
    cross_check_fail_count,
    validate_run,
)


class TestRemoteStartContract(unittest.TestCase):
    """Remote targets must not be started silently."""

    def test_remote_stopped_blocks(self):
        ok, why = allow_start(False, False, u"STOP")
        self.assertFalse(ok)
        self.assertIn(u"remote", why.lower())

    def test_remote_flag_overrides(self):
        ok, _ = allow_start(False, True, u"stop")
        self.assertTrue(ok)

    def test_local_may_start(self):
        self.assertTrue(allow_start(True, False, u"stop")[0])


class TestGreenEvidenceContract(unittest.TestCase):
    """A run is green only with positive evidence."""

    def test_all_checks_pass(self):
        self.assertIsNone(validate_run(2, 2, 5))

    def test_missing_suite_registration(self):
        self.assertIsNotNone(validate_run(0, 0, 1))

    def test_done_before_all_suites(self):
        self.assertIsNotNone(validate_run(3, 2, 5))

    def test_empty_run_is_red(self):
        self.assertIsNotNone(validate_run(1, 1, 0))

    def test_array_overflow_is_red(self):
        self.assertIsNotNone(validate_run(1, 1, MAX_CASES + 1))


class TestCounterCrossCheck(unittest.TestCase):
    def test_plc_and_read_agree(self):
        cases = [
            {u"eStatus": u"UINT#0"},
            {u"eStatus": u"UINT#1"},
            {u"eStatus": u"UINT#1"},
        ]
        self.assertIsNone(cross_check_fail_count(u"UINT#2", cases))

    def test_inconsistent_failcount(self):
        cases = [{u"eStatus": 1}]
        err = cross_check_fail_count(u"0", cases)
        self.assertIsNotNone(err)
        self.assertIn(u"mismatch", err)


if __name__ == "__main__":
    unittest.main()
