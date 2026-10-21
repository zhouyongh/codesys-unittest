# test_parse.py - L1 unit tests for ut_parse (pure helpers).
# Run: python -m unittest discover -s tests -v

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ut_parse import (
    MAX_CASES,
    allow_start,
    cross_check_fail_count,
    is_local_address,
    load_cfg,
    to_status,
    to_text,
    to_uint,
    validate_run,
)


class TestToUint(unittest.TestCase):
    def test_bool(self):
        self.assertEqual(to_uint(True), 1)
        self.assertEqual(to_uint(False), 0)

    def test_typed_prefix(self):
        self.assertEqual(to_uint(u"UINT#3"), 3)
        self.assertEqual(to_uint(u"LREAL#10"), 10)

    def test_plain(self):
        self.assertEqual(to_uint(u"12"), 12)
        self.assertEqual(to_uint(7), 7)

    def test_bool_words(self):
        self.assertEqual(to_uint(u"TRUE"), 1)
        self.assertEqual(to_uint(u"false"), 0)

    def test_unparsable_is_zero(self):
        self.assertEqual(to_uint(u"not-a-number"), 0)


class TestToText(unittest.TestCase):
    def test_none(self):
        self.assertEqual(to_text(None), u"")

    def test_strips_quotes(self):
        self.assertEqual(to_text(u"'hello'"), u"hello")

    def test_plain(self):
        self.assertEqual(to_text(u"abc"), u"abc")


class TestToStatus(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(to_status(u"0"), (0, u""))
        self.assertEqual(to_status(u"1"), (1, u""))
        self.assertEqual(to_status(u"2"), (2, u""))

    def test_typed_prefix(self):
        self.assertEqual(to_status(u"UINT#0"), (0, u""))
        self.assertEqual(to_status(u"UINT#1"), (1, u""))
        self.assertEqual(to_status(u"UINT#2"), (2, u""))

    def test_unreadable_is_fail(self):
        st, note = to_status(u"bogus")
        self.assertEqual(st, 1)
        self.assertIn(u"unreadable", note)

    def test_out_of_range_is_fail(self):
        st, note = to_status(u"9")
        self.assertEqual(st, 1)
        self.assertIn(u"unknown", note)


class TestLoadCfg(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _write(self, text):
        p = os.path.join(self.dir, "t.txt")
        f = open(p, "wb")
        try:
            f.write(text.encode("utf-8"))
        finally:
            f.close()
        return p

    def test_key_value(self):
        cfg = load_cfg(self._write(u"op=read\n# comment\nname = x\nempty=\n"))
        self.assertEqual(cfg[u"op"], u"read")
        self.assertEqual(cfg[u"name"], u"x")
        self.assertNotIn(u"comment", cfg)

    def test_utf8_values(self):
        cfg = load_cfg(self._write(u"log=日志路径\n"))
        self.assertEqual(cfg[u"log"], u"日志路径")


class TestAddressAndStart(unittest.TestCase):
    def test_local(self):
        self.assertTrue(is_local_address(u"127.0.0.1"))
        self.assertTrue(is_local_address(u"LOCALHOST"))
        self.assertFalse(is_local_address(u"192.168.1.10"))

    def test_start_local_stopped(self):
        ok, _why = allow_start(True, False, u"stop")
        self.assertTrue(ok)

    def test_start_remote_stopped_denied(self):
        ok, why = allow_start(False, False, u"stop")
        self.assertFalse(ok)
        self.assertIn(u"remote", why)

    def test_start_remote_allowed(self):
        ok, _ = allow_start(False, True, u"stop")
        self.assertTrue(ok)

    def test_already_run(self):
        ok, _ = allow_start(False, False, u"run")
        self.assertTrue(ok)


class TestValidateRun(unittest.TestCase):
    def test_ok(self):
        self.assertIsNone(validate_run(1, 1, 3))

    def test_no_suites(self):
        self.assertIsNotNone(validate_run(0, 0, 1))

    def test_partial_suites(self):
        self.assertIsNotNone(validate_run(2, 1, 3))

    def test_zero_cases(self):
        self.assertIsNotNone(validate_run(1, 1, 0))

    def test_overflow(self):
        self.assertIsNotNone(validate_run(1, 1, MAX_CASES + 1))


class TestCrossCheck(unittest.TestCase):
    def test_match(self):
        cases = [{u"eStatus": 1}, {u"eStatus": 0}, {u"eStatus": 1}]
        self.assertIsNone(cross_check_fail_count(u"UINT#2", cases))

    def test_typed_statuses(self):
        cases = [{u"eStatus": u"UINT#1"}, {u"eStatus": u"UINT#0"}]
        self.assertIsNone(cross_check_fail_count(1, cases))

    def test_mismatch(self):
        cases = [{u"eStatus": 1}]
        self.assertIsNotNone(cross_check_fail_count(0, cases))


if __name__ == "__main__":
    unittest.main()
