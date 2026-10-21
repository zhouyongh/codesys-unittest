# -*- coding: utf-8 -*-
# ut_parse.py - pure helpers shared by test_ops.py (IronPython 2.7) and
# host-side unit tests (CPython). No CODESYS API, no I/O side effects.
#
# Python 2/3 compatible on purpose: test_ops runs under IronPython 2.7 inside
# CODESYS; the test suite runs under CPython 3.

from __future__ import print_function

import codecs
import io

try:
    unicode  # noqa: B018  (Python 2 / IronPython)
except NameError:  # Python 3
    unicode = str  # noqa: A001

MAX_CASES = 64  # must match UT_MAX_CASES / g_astCases in lib/GVL_Test.st
LOCAL_ADDRESSES = (u"127.0.0.1", u"localhost", u"::1")


def load_cfg(path):
    """Parse key=value lines (UTF-8). # comments and blanks skipped."""
    cfg = {}
    f = codecs.open(path, u"r", u"utf-8")
    try:
        for line in f:
            line = line.strip()
            if not line or line.startswith(u"#") or u"=" not in line:
                continue
            k, v = line.split(u"=", 1)
            cfg[k.strip()] = v.strip()
    finally:
        f.close()
    return cfg


def to_uint(v):
    """Best-effort int from a CODESYS value (BOOL, UINT#3, '12', True...)."""
    if v is True or v is False:
        return 1 if v else 0
    s = unicode(v).strip()
    low = s.lower()
    if low in (u"true", u"yes", u"on"):
        return 1
    if low in (u"false", u"no", u"off", u""):
        return 0
    if u"#" in s:
        s = s.split(u"#")[-1]
    try:
        return int(float(s))
    except Exception:
        try:
            return int(s)
        except Exception:
            return 0


def to_text(v):
    """Unicode text from a CODESYS value; strips surrounding quotes."""
    if v is None:
        return u""
    try:
        s = unicode(v)
    except Exception:
        try:
            s = unicode(v, u"utf-8", u"replace")
        except Exception:
            s = unicode(repr(v))
    if len(s) >= 2 and s[0] == u"'" and s[-1] == u"'":
        s = s[1:-1]
    return s


def to_status(v):
    """Return (status, note). status: 0=pass 1=fail 2=skip.

    Unreadable or out-of-range values count as failures so a red run can
    never look green.
    """
    s = to_text(v).strip()
    # CODESYS prints typed values as UINT#0 / LREAL#1.0
    if u"#" in s:
        s = s.split(u"#")[-1].strip()
    try:
        n = int(float(s))
    except Exception:
        return (1, u"unreadable status %r" % (v,))
    if n not in (0, 1, 2):
        return (1, u"unknown status %d" % n)
    return (n, u"")


def is_local_address(address):
    a = to_text(address).strip().lower()
    return a in LOCAL_ADDRESSES


def allow_start(is_local, start_if_stopped, app_state):
    """Whether the runner may call oapp.start().

    Remote targets are never started unless explicitly allowed. Returns
    (ok, reason). reason is empty when ok is True.
    """
    st = to_text(app_state).strip().lower()
    if st in (u"run", u"running"):
        return (True, u"")
    if is_local or start_if_stopped:
        return (True, u"")
    return (False, u"application is %s on a remote target" % st)


def validate_run(suites_total, suites_done, case_count, max_cases=MAX_CASES):
    """Post-run counter checks. Return error string or None."""
    if suites_total == 0:
        return u"no suite registered (g_uiSuitesTotal=0)"
    if suites_done != suites_total:
        return (u"g_xDone fired after %s of %s suites"
                % (suites_done, suites_total))
    if case_count == 0:
        return u"no test cases recorded"
    if case_count > max_cases:
        return u"caseCount=%s exceeds the %d-slot array" % (case_count, max_cases)
    return None


def cross_check_fail_count(plc_fail, cases):
    """PLC fail counter must match the records that were read.

    cases: iterable of dicts with eStatus. Return error string or None.
    """
    computed = 0
    for c in cases:
        st, _note = to_status(c.get(u"eStatus"))
        if st == 1:
            computed += 1
    if to_uint(plc_fail) != computed:
        return (u"failCount mismatch: PLC reports %s, read %s"
                % (to_uint(plc_fail), computed))
    return None
