# test_cli.py - L3 smoke tests for ut.ps1 (no PLC needed).
# Run: python -m unittest discover -s tests -v
# Windows + PowerShell only; skipped elsewhere.
#
# The subprocess inherits CODESYS_UNITTEST_PYTHON=sys.executable so report.py
# is run by the same interpreter as the tests (no dependency on a "python"
# alias on PATH, which is a Store stub on some Windows machines).

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UT = os.path.join(ROOT, "ut.ps1")


def _run(args, timeout=60):
    cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", UT,
    ] + args
    env = dict(os.environ)
    env["CODESYS_UNITTEST_PYTHON"] = sys.executable
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
    )
    try:
        out, _ = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        out, _ = p.communicate()
        raise AssertionError("ut.ps1 timed out: %r\n%s" % (
            args, (out or b"").decode("utf-8", "replace")))
    text = out.decode("utf-8", "replace") if out else u""
    return p.returncode, text


@unittest.skipUnless(os.name == "nt", "ut.ps1 is Windows PowerShell")
class TestChangeGate(unittest.TestCase):
    def test_rejects_force_and_try(self):
        for change in ("Force", "Try", "force", "Download"):
            rc, text = _run(["run", "-Change", change, "-Project", r"D:\nope.project"])
            self.assertNotEqual(rc, 0, text)
            self.assertIn("rejected", text)

    def test_never_passes_gate(self):
        rc, text = _run(["run", "-Change", "Never", "-Project", r"D:\nope.project"])
        self.assertNotIn("rejected", text)
        self.assertNotEqual(rc, 0)  # project missing

    def test_keep_passes_gate(self):
        rc, text = _run(["run", "-Change", "Keep", "-Project", r"D:\nope.project"])
        self.assertNotIn("rejected", text)
        self.assertNotEqual(rc, 0)  # project missing


@unittest.skipUnless(os.name == "nt", "ut.ps1 is Windows PowerShell")
class TestMock(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_mock_green(self):
        rc, text = _run(["run", "-Mock", "-OutDir", self.dir])
        self.assertEqual(rc, 0, text)
        self.assertTrue(os.path.exists(os.path.join(self.dir, "report.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.dir, "junit.xml")))

    def test_mock_fail_red(self):
        rc, _text = _run(["run", "-MockFail", "-OutDir", self.dir])
        self.assertNotEqual(rc, 0)
        p = os.path.join(self.dir, "report.txt")
        f = open(p, "rb")
        try:
            txt = f.read().decode("utf-8")
        finally:
            f.close()
        self.assertIn("FAIL", txt)


@unittest.skipUnless(os.name == "nt", "ut.ps1 is Windows PowerShell")
class TestReportAndStatus(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_report_command(self):
        results = {
            "done": True,
            "caseCount": 1,
            "failCount": 0,
            "skipCount": 0,
            "cases": [{"sName": "S.t1", "eStatus": 0, "sMessage": "", "sSuite": "S"}],
        }
        src = os.path.join(self.dir, "results.json")
        f = open(src, "wb")
        try:
            f.write(json.dumps(results).encode("utf-8"))
        finally:
            f.close()
        out = os.path.join(self.dir, "out")
        rc, text = _run(["report", "-Results", src, "-OutDir", out])
        self.assertEqual(rc, 0, text)
        self.assertTrue(os.path.exists(os.path.join(out, "report.txt")))
        self.assertTrue(os.path.exists(os.path.join(out, "junit.xml")))

    def test_status_closed_port(self):
        rc, text = _run(["status", "-Port", "1"])
        self.assertNotEqual(rc, 0, text)
        self.assertIn("port_open=False", text)


if __name__ == "__main__":
    unittest.main()
