# test_protocol.py - template-content guards for lib/ (shipped ST protocol).
# Host-side constants (MAX_CASES) must agree with the GVL template; required
# symbols and the suite registry shape must stay intact when the templates
# are edited. Run: python -m unittest discover -s tests -v

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ut_parse import MAX_CASES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "lib")


def _read(rel):
    p = os.path.join(LIB, rel)
    f = open(p, "rb")
    try:
        raw = f.read()
    finally:
        f.close()
    return raw.decode("utf-8")


class TestGvlProtocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gvl = _read("GVL_Test.st")

    def test_max_cases_constant(self):
        m = re.search(r"UT_MAX_CASES\s*:\s*UINT\s*:=\s*(\d+)", self.gvl)
        self.assertIsNotNone(m, "UT_MAX_CASES not found in GVL_Test.st")
        self.assertEqual(int(m.group(1)), MAX_CASES)

    def test_case_array_bound(self):
        m = re.search(r"ARRAY\[1\.\.(\d+)\]\s*OF\s*UT_Case", self.gvl)
        self.assertIsNotNone(m, "g_astCases bound not found")
        self.assertEqual(int(m.group(1)), MAX_CASES)

    def test_required_symbols(self):
        for name in (
            "g_xReset", "g_xDone", "g_xOverflow",
            "g_uiCaseCount", "g_uiFailCount", "g_uiSkipCount",
            "g_uiSuitesTotal", "g_uiSuitesDone", "g_astCases",
            "g_sFilter", "g_sFirstFailure",
        ):
            self.assertIn(name, self.gvl, name)

    def test_status_values(self):
        self.assertIn("UT_PASS : UINT := 0", self.gvl)
        self.assertIn("UT_FAIL : UINT := 1", self.gvl)
        self.assertIn("UT_SKIP : UINT := 2", self.gvl)


class TestCaseRecord(unittest.TestCase):
    def test_fields_match_reader(self):
        text = _read("UT_Case.st")
        for field in ("sName", "eStatus", "sMessage"):
            self.assertIn(field, text)


class TestAssertProtocol(unittest.TestCase):
    def test_rec_records_cases_and_overflow(self):
        text = _read(os.path.join("FB_Assert", "Rec.st"))
        self.assertIn("g_uiCaseCount", text)
        self.assertIn("g_xOverflow := TRUE", text)
        self.assertIn("g_sFirstFailure", text)

    def test_begin_honours_reset(self):
        text = _read(os.path.join("FB_Assert", "Begin.st"))
        self.assertIn("GVL_Test.g_xReset", text)


class TestSuiteRegistry(unittest.TestCase):
    def test_prg_tests_sets_suite_total(self):
        text = _read("PRG_Tests.st")
        self.assertIn("g_uiSuitesTotal", text)

    def test_prg_tests_registers_at_least_one_suite(self):
        text = _read("PRG_Tests.st")
        # any FB_*_Test suite, not a specific sample name
        self.assertRegex(text, r"FB_\w+_Test")


if __name__ == "__main__":
    unittest.main()
