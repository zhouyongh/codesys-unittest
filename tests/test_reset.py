# test_reset.py - L2 tests for the reset/arm sequence (fake CODESYS IO).
# Run: python -m unittest discover -s tests -v

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ut_run import arm_run


class FakeIO(object):
    """Records calls and applies prepared values like the CODESYS app would."""

    def __init__(self, values=None, missing=(), fail=()):
        self.values = dict(values or {})
        self.missing = set(missing)
        self.fail = set(fail)
        self.calls = []
        self.pending = {}

    def set_prepared_value(self, name, value):
        if ("set", name) in self.fail:
            raise RuntimeError("set %s failed" % name)
        self.calls.append(("set", name, value))
        self.pending[name] = value

    def write_prepared_values(self):
        if "write" in self.fail:
            raise RuntimeError("write failed")
        self.calls.append(("write",))
        self.values.update(self.pending)
        self.pending = {}

    def read_value(self, name):
        if ("read", name) in self.fail:
            raise RuntimeError("read %s failed" % name)
        if name in self.missing:
            raise KeyError(name)
        self.calls.append(("read", name))
        return self.values.get(name, u"0")

    def sets(self):
        return [c for c in self.calls if c[0] == "set"]

    def last_reset_value(self):
        resets = [c for c in self.sets() if c[1] == u"GVL_Test.g_xReset"]
        return resets[-1][2] if resets else None


class StickyIO(FakeIO):
    """The PLC refuses to clear the counters (reset write still works)."""

    def write_prepared_values(self):
        self.calls.append(("write",))
        for name, value in self.pending.items():
            if name == u"GVL_Test.g_xReset":
                self.values[name] = value
        self.pending = {}


class FailReleaseIO(FakeIO):
    """Allow the arm write, reject the release write of g_xReset."""

    def set_prepared_value(self, name, value):
        if name == u"GVL_Test.g_xReset" and value == u"FALSE":
            raise RuntimeError("release failed")
        FakeIO.set_prepared_value(self, name, value)


class TestArmRun(unittest.TestCase):
    def test_default_hold_is_one_second(self):
        io = FakeIO()
        slept = []
        self.assertIsNone(arm_run(io, sleep=slept.append))
        self.assertEqual(slept, [1.0])

    def test_reset_order_hold_and_release(self):
        io = FakeIO()
        slept = []
        seen_at_sleep = []

        def fake_sleep(seconds):
            slept.append(seconds)
            seen_at_sleep.extend(io.calls)

        err = arm_run(io, min_hold=0.5, sleep=fake_sleep, log=lambda m: None)

        self.assertIsNone(err)
        self.assertEqual(slept, [0.5])
        # the reset is held before any counter is cleared
        self.assertFalse([c for c in seen_at_sleep
                          if len(c) > 1 and c[1] == u"GVL_Test.g_uiCaseCount"])

        sets = io.sets()
        self.assertEqual(sets[0], ("set", u"GVL_Test.g_xReset", u"TRUE"))
        self.assertEqual(sets[-1], ("set", u"GVL_Test.g_xReset", u"FALSE"))
        first = io.calls.index(sets[0])
        last = io.calls.index(sets[-1])
        clears = [i for i, c in enumerate(io.calls)
                  if c[0] == "set" and c[1] == u"GVL_Test.g_uiCaseCount"]
        self.assertTrue(first < clears[0] < last)
        self.assertEqual(io.values[u"GVL_Test.g_xReset"], u"FALSE")

    def test_clears_overflow_when_present(self):
        io = FakeIO(values={u"GVL_Test.g_xOverflow": u"1"})
        self.assertIsNone(arm_run(io, min_hold=0, sleep=lambda s: None))
        self.assertEqual(io.values[u"GVL_Test.g_xOverflow"], u"FALSE")

    def test_old_gvl_without_overflow_flag(self):
        io = FakeIO(missing={u"GVL_Test.g_xOverflow"})
        self.assertIsNone(arm_run(io, min_hold=0, sleep=lambda s: None))
        names = [c[1] for c in io.sets()]
        self.assertNotIn(u"GVL_Test.g_xOverflow", names)

    def test_ineffective_reset_is_error_and_released(self):
        io = StickyIO(values={
            u"GVL_Test.g_xDone": u"TRUE",
            u"GVL_Test.g_uiCaseCount": u"3",
        })
        err = arm_run(io, min_hold=0, sleep=lambda s: None)
        self.assertIsNotNone(err)
        self.assertIn(u"did not take effect", err)
        self.assertEqual(io.last_reset_value(), u"FALSE")

    def test_clear_failure_releases(self):
        io = FakeIO(fail={("set", u"GVL_Test.g_uiCaseCount")})
        err = arm_run(io, min_hold=0, sleep=lambda s: None)
        self.assertIsNotNone(err)
        self.assertIn(u"cannot clear", err)
        self.assertEqual(io.last_reset_value(), u"FALSE")

    def test_read_failure_releases(self):
        io = FakeIO(fail={("read", u"GVL_Test.g_xDone")})
        err = arm_run(io, min_hold=0, sleep=lambda s: None)
        self.assertIsNotNone(err)
        self.assertIn(u"cannot read", err)
        self.assertEqual(io.last_reset_value(), u"FALSE")

    def test_set_failure_is_reported(self):
        io = FakeIO(fail={("set", u"GVL_Test.g_xReset")})
        err = arm_run(io, min_hold=0, sleep=lambda s: None)
        self.assertIsNotNone(err)
        self.assertIn(u"cannot set", err)

    def test_clear_failure_and_release_failure_merged(self):
        # clear fails and the reset cannot be lifted: both facts in one error
        io = FailReleaseIO(fail={("set", u"GVL_Test.g_uiCaseCount")})
        err = arm_run(io, min_hold=0, sleep=lambda s: None)
        self.assertIsNotNone(err)
        self.assertIn(u"cannot clear", err)
        self.assertIn(u"cannot release", err)


if __name__ == "__main__":
    unittest.main()
