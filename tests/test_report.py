# test_report.py - L1 unit tests for report.py.
# Run: python -m unittest discover -s tests -v

import contextlib
import io
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

    def test_unfinished_run_is_red(self):
        cases = report.collect({u"done": False, u"cases": []})
        self.assertEqual(cases[-1][u"sName"], report.PIPELINE)
        self.assertIn(u"did not finish", cases[-1][u"sMessage"])


class TestReportFiles(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _write(self, obj, name="results.json"):
        p = os.path.join(self.dir, name)
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

    def _run_main(self, src, out=None):
        out = out or os.path.join(self.dir, "out")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = report.main(["report.py", src, out])
        return rc, buf.getvalue()

    def _junit(self):
        tree = ET.parse(os.path.join(self.dir, "out", "junit.xml"))
        return tree.getroot()

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
        rc, out = self._run_main(src)
        self.assertEqual(rc, 1, out)

        txt = self._read("report.txt")
        self.assertIn(u"WARN", txt)
        self.assertIn(u"FAIL  S.Test_bad", txt)
        self.assertIn(u"PASS  S.Test_ok", txt)

        suite = self._junit()
        self.assertEqual(suite.get("tests"), "2")
        self.assertEqual(suite.get("failures"), "1")
        self.assertEqual(len(suite.findall("testcase/failure")), 1)

    def test_zero_cases_exit_red(self):
        src = self._write({u"done": True, u"cases": []})
        rc, out = self._run_main(src)
        self.assertEqual(rc, 1, out)
        self.assertIn(u"pipeline", self._read("report.txt"))
        suite = self._junit()
        self.assertEqual(suite.get("tests"), "1")
        self.assertEqual(suite.get("failures"), "1")

    def test_green_exit_zero(self):
        src = self._write({
            u"done": True,
            u"cases": [{u"sName": u"S.t", u"eStatus": 0, u"sMessage": u""}],
        })
        rc, out = self._run_main(src)
        self.assertEqual(rc, 0, out)

    def test_unicode_messages(self):
        src = self._write({
            u"done": False,
            u"error": u"无效表达式",
            u"cases": [],
        })
        rc, out = self._run_main(src)
        self.assertEqual(rc, 1)
        self.assertIn(u"无效表达式", self._read("report.txt"))

    def test_missing_results_file(self):
        rc, out = self._run_main(os.path.join(self.dir, "nope.json"))
        self.assertEqual(rc, 1)
        self.assertIn(u"ERR results not found", out)

    def test_malformed_json(self):
        src = os.path.join(self.dir, "bad.json")
        f = open(src, "wb")
        try:
            f.write(b"{not json")
        finally:
            f.close()
        rc, out = self._run_main(src)
        self.assertEqual(rc, 1)
        self.assertIn(u"ERR cannot read", out)

    def test_unfinished_run_exit_red(self):
        src = self._write({u"done": False, u"cases": []})
        rc, out = self._run_main(src)
        self.assertEqual(rc, 1, out)
        self.assertIn(u"did not finish", self._read("report.txt"))
        self.assertEqual(self._junit().get("failures"), "1")

    def test_skipped_counts(self):
        src = self._write({
            u"done": True,
            u"cases": [
                {u"sName": u"S.t1", u"eStatus": 0, u"sMessage": u""},
                {u"sName": u"S.t2", u"eStatus": 2, u"sMessage": u"not here"},
            ],
        })
        rc, out = self._run_main(src)
        self.assertEqual(rc, 0, out)
        suite = self._junit()
        self.assertEqual(suite.get("tests"), "2")
        self.assertEqual(suite.get("skipped"), "1")
        skipped = suite.findall("testcase/skipped")
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0].get("message"), u"not here")

    def test_pipeline_error_junit_counts(self):
        src = self._write({u"done": False, u"error": u"login failed", u"cases": []})
        rc, _out = self._run_main(src)
        self.assertEqual(rc, 1)
        suite = self._junit()
        self.assertEqual(suite.get("tests"), "1")
        self.assertEqual(suite.get("failures"), "1")
        failure = suite.find("testcase/failure")
        self.assertIsNotNone(failure)
        self.assertEqual(failure.get("type"), "PipelineError")


if __name__ == "__main__":
    unittest.main()
