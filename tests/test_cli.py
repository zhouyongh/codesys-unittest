# test_cli.py - L3 smoke tests for ut.ps1 parameter gates (no PLC needed).
# Run: python -m unittest discover -s tests -v
# Windows + PowerShell only; skipped elsewhere.

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
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    out, _ = p.communicate(timeout=timeout)
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


if __name__ == "__main__":
    unittest.main()
