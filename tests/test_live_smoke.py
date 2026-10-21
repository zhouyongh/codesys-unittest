# test_live_smoke.py - L5: live run against a real CODESYS target.
# Run (PowerShell):
#   $env:CODESYS_UNITTEST_LIVE = "1"
#   $env:CODESYS_UNITTEST_PROJECT = "D:\repo\projects\App.project"
#   $env:CODESYS_UNITTEST_USERFILE = "D:\repo\user.txt"
#   python -m unittest discover -s tests -p "test_live_smoke.py" -v
#
# Skipped by default. The project must already contain the suites and be
# downloaded; this test does not import, download or start a remote runtime.

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UT = os.path.join(ROOT, "ut.ps1")

LIVE = os.environ.get("CODESYS_UNITTEST_LIVE") == "1"
PROJECT = os.environ.get("CODESYS_UNITTEST_PROJECT", "")
USERFILE = os.environ.get("CODESYS_UNITTEST_USERFILE", "")
HAS_CREDS = bool(USERFILE) or bool(os.environ.get("CODESYS_UNITTEST_USER"))
REASON = ("live test: set CODESYS_UNITTEST_LIVE=1, CODESYS_UNITTEST_PROJECT "
          "and CODESYS_UNITTEST_USERFILE")


@unittest.skipUnless(os.name == "nt", "ut.ps1 is Windows PowerShell")
@unittest.skipUnless(LIVE and PROJECT and HAS_CREDS, REASON)
class TestLiveSmoke(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.out, True)

    def _run(self):
        args = [
            "run",
            "-Project", PROJECT,
            "-OutDir", self.out,
            "-TimeoutSec", "180",
        ]
        if USERFILE:
            args += ["-UserFile", USERFILE]
        if os.environ.get("CODESYS_UNITTEST_ADDRESS"):
            args += ["-Address", os.environ["CODESYS_UNITTEST_ADDRESS"]]
        if os.environ.get("CODESYS_UNITTEST_PORT"):
            args += ["-Port", os.environ["CODESYS_UNITTEST_PORT"]]

        env = dict(os.environ)
        env["CODESYS_UNITTEST_PYTHON"] = sys.executable
        p = subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", UT] + args,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
        )
        try:
            out, _ = p.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            p.kill()
            out, _ = p.communicate()
            raise AssertionError("live run hung: " + (out or b"").decode("utf-8", "replace"))
        return p.returncode, (out or b"").decode("utf-8", "replace")

    def _report(self):
        path = os.path.join(self.out, "report.txt")
        f = open(path, "rb")
        try:
            return f.read().decode("utf-8")
        finally:
            f.close()

    def test_two_runs_in_a_row_are_green(self):
        counts = []
        for run in (1, 2):
            rc, text = self._run()
            self.assertEqual(rc, 0, "run %d failed:\n%s" % (run, text))
            report = self._report()
            m = re.search(r"(\d+) cases, (\d+) failed, (\d+) skipped", report)
            self.assertIsNotNone(m, report)
            cases, failed, _skipped = [int(x) for x in m.groups()]
            self.assertGreater(cases, 0, report)
            self.assertEqual(failed, 0, report)
            counts.append(cases)

        self.assertEqual(counts[0], counts[1], "case count changed between runs")
        expected = os.environ.get("CODESYS_UNITTEST_EXPECT_CASES")
        if expected:
            self.assertEqual(counts[0], int(expected), "unexpected case count")


if __name__ == "__main__":
    unittest.main()
