# test_cli_real.py - L3: exercise ut.ps1's real run path without CODESYS.
# Run: python -m unittest discover -s tests -v
#
# A fake "CODESYS" .cmd and a fake ops script are injected through the test
# hooks in ut.ps1, so the launch, target.txt, watchdog, results copy and report
# are all real. A listener on 127.0.0.2 stands in for a remote runtime.

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UT = os.path.join(ROOT, "ut.ps1")

FAKE_OPS = r'''# -*- coding: utf-8 -*-
import json
import os
import time

target = os.environ["CODESYS_UNITTEST_TARGET"]
text = open(target, "r", encoding="utf-8").read()
copy = os.environ.get("FAKE_TARGET_COPY")
if copy:
    open(copy, "w", encoding="utf-8").write(text)

sleep = os.environ.get("FAKE_SLEEP")
if sleep:
    time.sleep(float(sleep))
    raise SystemExit(0)

cfg = {}
for line in text.splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        cfg[k.strip()] = v.strip()

cases = [
    {"sName": "Stub.Test_one", "eStatus": 0, "sMessage": "", "sSuite": "Stub"},
    {"sName": "Stub.Test_two", "eStatus": 0, "sMessage": "", "sSuite": "Stub"},
]
out = {
    "done": True,
    "caseCount": len(cases),
    "failCount": 0,
    "skipCount": 0,
    "durationSec": 0.1,
    "cases": cases,
}
open(cfg["result"], "w", encoding="utf-8").write(json.dumps(out))
'''

FAKE_CMD = r'''@echo off
"%CODESYS_UNITTEST_PYTHON%" "%FAKE_OPS_PY%"
exit /b %ERRORLEVEL%
'''


@unittest.skipUnless(os.name == "nt", "ut.ps1 is Windows PowerShell")
class TestRealRunPath(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)

        self.project = os.path.join(self.dir, "App.project")
        f = open(self.project, "w")
        try:
            f.write("fake project")
        finally:
            f.close()

        self.user = os.path.join(self.dir, "user.txt")
        f = open(self.user, "w")
        try:
            f.write("alice\nsecret-password\n")
        finally:
            f.close()

        self.out = os.path.join(self.dir, "out")
        self.target_copy = os.path.join(self.dir, "target-copy.txt")
        self.fake_ops = os.path.join(self.dir, "fake_ops.py")
        f = open(self.fake_ops, "w")
        try:
            f.write(FAKE_OPS)
        finally:
            f.close()

        self.fake_cmd = os.path.join(self.dir, "fake_codesys.cmd")
        f = open(self.fake_cmd, "w")
        try:
            f.write(FAKE_CMD)
        finally:
            f.close()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.bind(("127.0.0.2", 0))
            self.sock.listen(1)
        except OSError as e:
            self.sock.close()
            self.skipTest("cannot bind 127.0.0.2: %s" % e)
        self.addCleanup(self.sock.close)
        self.port = self.sock.getsockname()[1]

        self.profile = os.path.join(self.dir, "profile")
        os.makedirs(self.profile)

        self.env = dict(os.environ)
        self.env.update({
            "CODESYS_UNITTEST_EXE": self.fake_cmd,
            "CODESYS_UNITTEST_PROFILE": "Test",
            "CODESYS_UNITTEST_OPS": self.fake_ops,
            "CODESYS_UNITTEST_PYTHON": sys.executable,
            "FAKE_OPS_PY": self.fake_ops,
            "FAKE_TARGET_COPY": self.target_copy,
            "FAKE_SLEEP": "",
            "CODESYS_UNITTEST_WATCHDOG_SEC": "",
            "USERPROFILE": self.profile,
        })

    def _run(self, extra=None, timeout=120):
        env = dict(self.env)
        if extra:
            env.update(extra)
        args = [
            "run",
            "-Project", self.project,
            "-UserFile", self.user,
            "-Address", "127.0.0.2",
            "-Port", str(self.port),
            "-OutDir", self.out,
            "-TimeoutSec", "5",
        ]
        p = subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", UT] + args,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
        )
        try:
            out, _ = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            out, _ = p.communicate()
            raise AssertionError("ut.ps1 hung: " + (out or b"").decode("utf-8", "replace"))
        return p.returncode, (out or b"").decode("utf-8", "replace")

    def test_run_path_reports_and_keeps_password_out_of_target(self):
        rc, text = self._run()
        self.assertEqual(rc, 0, text)
        self.assertIn("2 cases", text)
        self.assertTrue(os.path.exists(os.path.join(self.out, "report.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.out, "junit.xml")))
        self.assertTrue(os.path.exists(self.target_copy))

        f = open(self.target_copy, "r", encoding="utf-8")
        try:
            target = f.read()
        finally:
            f.close()
        self.assertIn("change=Never", target)
        self.assertIn("start_if_stopped=0", target)
        self.assertIn("port=%d" % self.port, target)
        self.assertNotIn("secret-password", target)
        self.assertNotIn("alice", target)

    def test_start_flag_is_written_for_remote(self):
        # -StartIfStopped must reach target.txt even for a remote target.
        env = dict(self.env)
        p = subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", UT,
             "run", "-Project", self.project, "-UserFile", self.user,
             "-Address", "127.0.0.2", "-Port", str(self.port),
             "-OutDir", self.out, "-TimeoutSec", "5", "-StartIfStopped"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
        )
        out, _ = p.communicate(timeout=120)
        self.assertEqual(p.returncode, 0, (out or b"").decode("utf-8", "replace"))
        f = open(self.target_copy, "r", encoding="utf-8")
        try:
            self.assertIn("start_if_stopped=1", f.read())
        finally:
            f.close()

    def test_watchdog_kills_the_fake_runner(self):
        rc, text = self._run(
            extra={"FAKE_SLEEP": "30", "CODESYS_UNITTEST_WATCHDOG_SEC": "2"},
            timeout=60,
        )
        self.assertNotEqual(rc, 0, text)
        self.assertIn("timed out", text)


if __name__ == "__main__":
    unittest.main()
