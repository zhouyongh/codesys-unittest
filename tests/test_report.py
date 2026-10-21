# test_report.py - L1 unit tests for report.py.
# Run: python -m unittest discover -s tests -v

import json
import os
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import report


class TestStatusOf(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(report.status_of({u"eStatus": 0}), 0)
        self.assertEqual(report.status_of({u"eStatus": 1}), 1)
        self.assertEqual(report.status_of({u"eStatus": 2}), 2)

    def test_unknown_is_fail(self):
        self.assertEqual(report.status_of({u"eStatus": 9}), 1)
        self.assertEqual(report.status_of({}), 1)


class TestCollect(unittest.TestCase):
    def test_done_with_cases(self):
        cases = report.collect({
            u"done": True,
            u"cases": [{u"sName": u"A.t1", u"eStatus": 0}],
        })
        self.assertEqual(len(cases), 1)

    def test_pipeline_error_appended(self):
        cases = report.collect({
            u"done": False,
            u"error": u"boom",
            u"cases": [{u"sName": u"A.t1", u"eStatus": 0}],
        })
        self.assertEqual(cases[-1][u"sName"], report.PIPELINE)
        self.assertEqual(cases[-1][u"eStatus"], 1)
        self.assertIn(u"boom", cases[-1][u"sMessage"])

    def test_zero_cases_is_red(self):
        cases = report.collect({u"done": True, u"cases": []})
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0][u"sName"], report.PIPELINE)
        self.assertEqual(cases[0][u"eStatus"], 1)


class TestReportFiles(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _write(self, obj):
        p = os.path.join(self.dir, "results.json")
        f = open(p, "wb")
        try:
            f.write(json.dumps(obj).encode("utf-8"))
        finally:
            f.close()
        return p

    def _read(self, name):
        p = os.path.join(self.dir, "out", name)
        f = open(p, "rb")
        try:
            return f.read().decode("utf-8")
        finally:
            f.close()

    def test_text_and_junit(self):
        src = self._write({
            u"done": True,
            u"caseCount": 2,
            u"failCount": 1,
            u"skipCount": 0,
            u"warn": u"skipCount mismatch",
            u"cases": [
                {u"sName": u"S.Test_ok", u"eStatus": 0, u"sMessage": u"", u"sSuite": u"S"},
                {u"sName": u"S.Test_bad", u"eStatus": 1, u"sMessage": u"mismatch",
                 u"sSuite": u"S"},
            ],
        })
        out = os.path.join(self.dir, "out")
        rc = report.main(["report.py", src, out])
        self.assertEqual(rc, 1)

        txt = self._read("report.txt")
        self.assertIn(u"WARN", txt)
        self.assertIn(u"FAIL  S.Test_bad", txt)
        self.assertIn(u"PASS  S.Test_ok", txt)

        tree = ET.parse(os.path.join(out, "junit.xml"))
        suite = tree.getroot()
        self.assertEqual(suite.get("tests"), "2")
        self.assertEqual(suite.get("failures"), "1")

    def test_zero_cases_exit_red(self):
        src = self._write({u"done": True, u"cases": []})
        out = os.path.join(self.dir, "out")
        self.assertEqual(report.main(["report.py", src, out]), 1)
        self.assertIn(u"pipeline", self._read("report.txt"))

    def test_green_exit_zero(self):
        src = self._write({
            u"done": True,
            u"cases": [{u"sName": u"S.t", u"eStatus": 0, u"sMessage": u""}],
        })
        out = os.path.join(self.dir, "out")
        self.assertEqual(report.main(["report.py", src, out]), 0)

    def test_unicode_messages(self):
        src = self._write({
            u"done": False,
            u"error": u"无效表达式",
            u"cases": [],
        })
        out = os.path.join(self.dir, "out")
        report.main(["report.py", src, out])
        self.assertIn(u"无效表达式", self._read("report.txt"))


if __name__ == "__main__":
    unittest.main()
