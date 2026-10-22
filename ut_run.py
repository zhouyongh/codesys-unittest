# -*- coding: utf-8 -*-
# ut_run.py - the reset/arm sequence used by test_ops.py.
#
# The online application is injected (set_prepared_value / write_prepared_values
# / read_value), so the sequence can be tested with a fake under CPython while
# the real runner uses the CODESYS Scripting Engine object. Python 2/3
# compatible: test_ops.py runs under IronPython 2.7 inside CODESYS.

from __future__ import print_function

import time

from ut_parse import to_uint

# Cleared while g_xReset is held. g_xOverflow is handled separately so a
# project with an older GVL_Test still works.
_CLEAR = (
    (u"GVL_Test.g_xDone", u"FALSE"),
    (u"GVL_Test.g_uiCaseCount", u"0"),
    (u"GVL_Test.g_uiFailCount", u"0"),
    (u"GVL_Test.g_uiSkipCount", u"0"),
    (u"GVL_Test.g_uiSuitesDone", u"0"),
)


def _has_field(io, name):
    try:
        io.read_value(name)
        return True
    except Exception:
        return False


def _has_overflow_flag(io):
    return _has_field(io, u"GVL_Test.g_xOverflow")


def _try_release(io, log):
    try:
        io.set_prepared_value(u"GVL_Test.g_xReset", u"FALSE")
        io.write_prepared_values()
        return None
    except Exception as e:
        return u"cannot release GVL_Test.g_xReset: %r" % (e,)


def _fail_with_release(io, log, err):
    """Return err, appending a release failure when the reset cannot be lifted."""
    rel = _try_release(io, log)
    if rel:
        return u"%s; also %s" % (err, rel)
    return err


def arm_run(io, min_hold=1.0, sleep=None, log=None):
    """Reset the previous run, clear the counters, prove the clear, release.

    ``io`` is the CODESYS online application (or a fake in tests):
    ``set_prepared_value(name, value)``, ``write_prepared_values()`` and
    ``read_value(name)``.

    The reset is held for at least ``min_hold`` seconds. That hold is the only
    guarantee that a task cycle observes ``g_xReset`` before it is released;
    the counter read-back proves the host wrote the clear, not that the PLC
    processed it. Keeping the hold short here makes recovery from a hung suite
    flaky, so do not turn it into a "poll until the counters are zero" loop.

    Returns None on success, or an error string (the reset is released on every
    failure path so a failed run does not leave the PLC frozen in reset).
    """
    sleep = sleep or time.sleep
    log = log or (lambda msg: None)

    try:
        io.set_prepared_value(u"GVL_Test.g_xReset", u"TRUE")
        io.write_prepared_values()
    except Exception as e:
        return u"cannot set GVL_Test.g_xReset: %r" % (e,)

    # Fixed minimum hold. Do not replace this with a counter poll: the
    # counters still hold the previous run's values until the clear below.
    sleep(min_hold)

    has_overflow = _has_overflow_flag(io)
    has_first_failure = _has_field(io, u"GVL_Test.g_sFirstFailure")
    try:
        for name, value in _CLEAR:
            io.set_prepared_value(name, value)
        if has_overflow:
            io.set_prepared_value(u"GVL_Test.g_xOverflow", u"FALSE")
        if has_first_failure:
            io.set_prepared_value(u"GVL_Test.g_sFirstFailure", u"''")
        io.write_prepared_values()
    except Exception as e:
        return _fail_with_release(io, log, u"cannot clear GVL_Test counters: %r" % (e,))

    try:
        done0 = to_uint(io.read_value(u"GVL_Test.g_xDone"))
        n0 = to_uint(io.read_value(u"GVL_Test.g_uiCaseCount"))
        f0 = to_uint(io.read_value(u"GVL_Test.g_uiFailCount"))
    except Exception as e:
        return _fail_with_release(io, log, u"cannot read GVL_Test back after reset: %r" % (e,))

    if done0 != 0 or n0 != 0 or f0 != 0:
        return _fail_with_release(
            io, log,
            (u"reset did not take effect (g_xDone=%s caseCount=%s failCount=%s) - "
             u"is PRG_Tests running?" % (done0, n0, f0)))

    try:
        io.set_prepared_value(u"GVL_Test.g_xReset", u"FALSE")
        io.write_prepared_values()
    except Exception as e:
        return u"cannot release GVL_Test.g_xReset: %r" % (e,)
    return None
