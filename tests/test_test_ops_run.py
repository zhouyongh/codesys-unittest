# test_test_ops_run.py - L4: run_tests() against a fake CODESYS Scripting API.
# Run: python -m unittest discover -s tests -v
#
# No CODESYS and no PLC: the project tree, online application and GVL are fakes.
# This covers the orchestration (login -> start policy -> reset -> poll ->
# validate -> read cases -> results.json) that the pure-helper tests cannot.

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import test_ops


class Node(object):
    def __init__(self, name, children=None, is_application=False, is_device=False):
        self.name = name
        self.children = list(children or [])
        self.is_application = is_application
        self.is_device = is_device

    def get_name(self):
        return self.name

    def get_children(self):
        return self.children


class FakeSettings(object):
    def __init__(self):
        self.device_name = u""
        self.device_address = u""
        self.gateway_guid = u""


class FakeGateway(object):
    def __init__(self, name=u"Gateway-1"):
        self.name = name
        self.guid = u"gw-guid"


class FakeGateways(object):
    def __init__(self):
        self.gw = FakeGateway()

    def find_with_name(self, name):
        return [self.gw] if name == self.gw.name else []

    def __getitem__(self, index):
        return self.gw


class FakeDevice(Node):
    def __init__(self):
        Node.__init__(self, u"Device", is_device=True)
        self.settings = FakeSettings()

    def get_device_communication_settings(self):
        return self.settings

    def set_gateway_and_ip_address(self, gateway, address, port):
        self.settings.gateway_guid = gateway.guid
        self.settings.device_address = u"%s:%s" % (address, port)

    def set_gateway_and_device_name(self, gateway, name):
        self.settings.device_name = name


class FakeProjects(object):
    def __init__(self, project):
        self.project = project

    def open(self, path):
        return self.project


class FakeOnlineDevice(object):
    def __init__(self):
        self.connected = False

    def connect(self):
        self.connected = True


class FakeApp(object):
    """Minimal online application with a writable GVL_Test."""

    def __init__(self):
        self.values = {
            u"GVL_Test.g_xDone": False,
            u"GVL_Test.g_uiCaseCount": 0,
            u"GVL_Test.g_uiFailCount": 0,
            u"GVL_Test.g_uiSkipCount": 0,
            u"GVL_Test.g_uiSuitesTotal": 0,
            u"GVL_Test.g_uiSuitesDone": 0,
            u"GVL_Test.g_xOverflow": False,
            u"GVL_Test.g_xReset": False,
        }
        self.cases = []
        self.pending = {}
        self.state = u"run"
        self.login_calls = []
        self.start_calls = 0
        self.fail_login = False
        self.fail_reads = set()
        self.ignore_clear = False
        self.auto_finish = True
        self.finish_plan = None

    @property
    def application_state(self):
        return self.state

    def login(self, change, delete_foreign):
        if self.fail_login:
            raise RuntimeError(u"login denied")
        self.login_calls.append((change, delete_foreign))

    def start(self):
        self.start_calls += 1
        self.state = u"run"

    def set_prepared_value(self, name, value):
        self.pending[name] = value

    def write_prepared_values(self):
        if self.ignore_clear:
            if u"GVL_Test.g_xReset" in self.pending:
                self.values[u"GVL_Test.g_xReset"] = self.pending[u"GVL_Test.g_xReset"]
            self.pending = {}
            return
        self.values.update(self.pending)
        reset = self.pending.get(u"GVL_Test.g_xReset")
        self.pending = {}
        if reset == u"FALSE" and self.auto_finish:
            self._finish()

    def _finish(self):
        plan = self.finish_plan or {}
        cases = plan.get("cases")
        if cases is None:
            cases = [{u"sName": u"Suite.Test_ok", u"eStatus": 0, u"sMessage": u""}]
        self.cases = cases
        self.values[u"GVL_Test.g_xDone"] = True
        self.values[u"GVL_Test.g_uiCaseCount"] = len(cases)
        self.values[u"GVL_Test.g_uiFailCount"] = plan.get(
            "fail_count", len([c for c in cases if str(c.get(u"eStatus")) in (u"1", u"UINT#1")]))
        self.values[u"GVL_Test.g_uiSkipCount"] = plan.get(
            "skip_count", len([c for c in cases if str(c.get(u"eStatus")) in (u"2", u"UINT#2")]))
        self.values[u"GVL_Test.g_uiSuitesTotal"] = plan.get("total", 1)
        self.values[u"GVL_Test.g_uiSuitesDone"] = plan.get("done", 1)
        self.values[u"GVL_Test.g_xOverflow"] = plan.get("overflow", False)

    def read_value(self, name):
        if name in self.fail_reads:
            raise RuntimeError(u"read failed: %s" % name)
        if name.startswith(u"GVL_Test.g_astCases["):
            head, _, field = name.partition(u"].")
            index = int(head[len(u"GVL_Test.g_astCases["):])
            if index < 1 or index > len(self.cases):
                raise RuntimeError(u"bad case index %d" % index)
            return self.cases[index - 1].get(field, u"")
        return self.values.get(name, 0)


class FakeOnline(object):
    def __init__(self, app):
        self.app = app
        self.gateways = FakeGateways()
        self.credentials = None

    def set_default_credentials(self, user, password):
        self.credentials = (user, password)

    def create_online_device(self, device=None):
        return FakeOnlineDevice()

    def create_online_application(self, app_node):
        return self.app


class FakeOptions(object):
    Never = u"Never"
    Keep = u"Keep"
    Try = u"Try"
    Force = u"Force"


class TestRunTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)

        app_node = Node(u"Application", is_application=True)
        device = FakeDevice()
        device.children = [app_node]
        project = Node(u"Project", children=[device])

        self.app = FakeApp()
        self.projects = FakeProjects(project)
        self.online = FakeOnline(self.app)

        # restore globals so a parallel or later suite is not polluted
        def _restore(name, value):
            setattr(test_ops, name, value)

        for name, value in (
            ("projects", getattr(test_ops, "projects", None)),
            ("online", getattr(test_ops, "online", None)),
            ("OnlineChangeOption", getattr(test_ops, "OnlineChangeOption", None)),
        ):
            self.addCleanup(_restore, name, value)

        test_ops.projects = self.projects
        test_ops.online = self.online
        test_ops.OnlineChangeOption = FakeOptions

        # ut_run and the poll loop use the shared time module.
        patcher = mock.patch("time.sleep", lambda seconds: None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _target(self, **cfg):
        proj = os.path.join(self.dir, "App.project")
        f = open(proj, "w")
        try:
            f.write("fake")
        finally:
            f.close()
        values = {
            "project": proj,
            "result": os.path.join(self.dir, "results.json"),
            "log": os.path.join(self.dir, "ut_log.txt"),
            "address": cfg.get("address", "127.0.0.1"),
            "port": "11740",
            "change": cfg.get("change", "Never"),
            "timeout_sec": str(cfg.get("timeout", 1)),
            "start_if_stopped": str(cfg.get("start_if_stopped", 0)),
        }
        path = os.path.join(self.dir, "target.txt")
        f = open(path, "w")
        try:
            for key in sorted(values):
                f.write(u"%s=%s\n" % (key, values[key]))
        finally:
            f.close()
        return path

    def _run(self, **cfg):
        target = self._target(**cfg)
        test_ops.configure(target)
        test_ops.projects = self.projects
        test_ops.online = self.online
        test_ops.run_tests()
        f = open(test_ops.RESULT, "rb")
        try:
            return json.loads(f.read().decode("utf-8"))
        finally:
            f.close()

    def test_success_reads_cases_and_writes_json(self):
        cases = [
            {u"sName": u"A.t1", u"eStatus": 0, u"sMessage": u""},
            {u"sName": u"A.t2", u"eStatus": 0, u"sMessage": u""},
            {u"sName": u"A.t3", u"eStatus": 0, u"sMessage": u""},
        ]
        self.app.finish_plan = {"cases": cases}
        out = self._run()
        self.assertTrue(out["done"])
        self.assertEqual(out["caseCount"], 3)
        self.assertEqual(out["failCount"], 0)
        self.assertEqual([c["sName"] for c in out["cases"]], [u"A.t1", u"A.t2", u"A.t3"])
        self.assertEqual(self.app.login_calls, [(u"Never", False)])

    def test_login_failure_is_reported(self):
        self.app.fail_login = True
        out = self._run()
        self.assertFalse(out["done"])
        self.assertIn(u"login failed", out["error"])

    def test_missing_gvl_is_reported(self):
        self.app.fail_reads.add(u"GVL_Test.g_uiCaseCount")
        out = self._run()
        self.assertFalse(out["done"])
        self.assertIn(u"GVL_Test protocol not found", out["error"])

    def test_ineffective_reset_is_reported(self):
        self.app.ignore_clear = True
        self.app.values[u"GVL_Test.g_xDone"] = True
        self.app.values[u"GVL_Test.g_uiCaseCount"] = 3
        out = self._run()
        self.assertFalse(out["done"])
        self.assertIn(u"reset did not take effect", out["error"])

    def test_timeout_is_reported(self):
        self.app.auto_finish = False
        out = self._run(timeout=0)
        self.assertFalse(out["done"])
        self.assertIn(u"timeout", out["error"])

    def test_zero_cases_is_failure(self):
        self.app.finish_plan = {"cases": []}
        out = self._run()
        self.assertFalse(out["done"])
        self.assertIn(u"no test cases recorded", out["error"])

    def test_suite_mismatch_is_failure(self):
        self.app.finish_plan = {"cases": [{u"sName": u"A.t", u"eStatus": 0, u"sMessage": u""}],
                                "total": 2, "done": 1}
        out = self._run()
        self.assertFalse(out["done"])
        self.assertIn(u"1 of 2 suites", out["error"])

    def test_overflow_is_failure(self):
        self.app.finish_plan = {"cases": [{u"sName": u"A.t", u"eStatus": 0, u"sMessage": u""}],
                                "overflow": True}
        out = self._run()
        self.assertFalse(out["done"])
        self.assertIn(u"g_xOverflow", out["error"])

    def test_fail_count_mismatch_is_failure(self):
        self.app.finish_plan = {
            "cases": [{u"sName": u"A.t", u"eStatus": 1, u"sMessage": u"x"}],
            "fail_count": 2,
        }
        out = self._run()
        self.assertFalse(out["done"])
        self.assertIn(u"failCount mismatch", out["error"])

    def test_skip_mismatch_is_warn_not_failure(self):
        self.app.finish_plan = {
            "cases": [
                {u"sName": u"A.ok", u"eStatus": 0, u"sMessage": u""},
                {u"sName": u"A.slow", u"eStatus": 2, u"sMessage": u"skip"},
            ],
            "skip_count": 0,
        }
        out = self._run()
        self.assertTrue(out["done"])
        self.assertIn(u"skipCount mismatch", out["warn"])
        self.assertEqual(out["skipCount"], 1)

    def test_remote_stopped_is_not_started(self):
        self.app.state = u"stop"
        out = self._run(address="10.0.0.5")
        self.assertFalse(out["done"])
        self.assertIn(u"remote target", out["error"])
        self.assertEqual(self.app.start_calls, 0)

    def test_local_stopped_is_started(self):
        self.app.state = u"stop"
        out = self._run(address="127.0.0.1")
        self.assertTrue(out["done"])
        self.assertEqual(self.app.start_calls, 1)

    def test_case_read_failure_is_reported(self):
        cases = [
            {u"sName": u"A.t1", u"eStatus": 0, u"sMessage": u""},
            {u"sName": u"A.t2", u"eStatus": 0, u"sMessage": u""},
        ]
        self.app.finish_plan = {"cases": cases}
        self.app.fail_reads.add(u"GVL_Test.g_astCases[2].sName")
        out = self._run()
        self.assertFalse(out["done"])
        self.assertIn(u"cannot read case 2", out["error"])

    def test_typed_values_are_normalized(self):
        self.app.finish_plan = {
            "cases": [{u"sName": u"'A.b'", u"eStatus": u"UINT#1", u"sMessage": u"x"}],
            "fail_count": 1,
        }
        out = self._run()
        self.assertTrue(out["done"])
        self.assertEqual(out["cases"][0]["sName"], u"A.b")
        self.assertEqual(out["cases"][0]["eStatus"], 1)
        self.assertEqual(out["cases"][0]["sSuite"], u"A")
        self.assertEqual(out["failCount"], 1)

    def test_change_keep_is_passed_to_login(self):
        self.app.finish_plan = {"cases": [{u"sName": u"A.t", u"eStatus": 0, u"sMessage": u""}]}
        self._run(change="Keep")
        self.assertEqual(self.app.login_calls, [(u"Keep", False)])


if __name__ == "__main__":
    unittest.main()
