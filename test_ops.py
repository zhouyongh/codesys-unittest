# -*- coding: utf-8 -*-
# test_ops.py - codesys-unittest backend (CODESYS --runscript, IronPython 2.7)
# Polls GVL_Test.g_xDone and reads case records into results.json.
#
# target.txt keys (UTF-8):
#   project=<abs .project path>
#   result=<output json path>
#   log=<log file>
#   device= app= address= port=
#   timeout_sec=60
#   change=Never|Keep          (login only; Force/Try rejected by ut.ps1)
#   start_if_stopped=0|1       (1 = start the app when it is not RUN)
#
# Login credentials are NOT read from target.txt. They come from
#   CODESYS_UNITTEST_USER / CODESYS_UNITTEST_PASSWORD  or the codesys-connect
#   session file. Never write passwords into target.txt.
#
# Output results.json (UTF-8):
#   { "done": true, "caseCount": N, "failCount": N, "skipCount": N,
#     "durationSec": S, "cases": [ {"sName","eStatus","sMessage","sSuite"} ] }
#   On any pipeline problem: { "done": false, "error": "...", "cases": [...] }
#
# A run is only green when there is positive evidence that it really ran:
#   reset read back as clear, at least one case, all registered suites done,
#   every case readable and the PLC fail counter matching what was read.

import codecs
import json
import os
import sys
import time
import traceback

try:
    unicode  # noqa: B018  (IronPython 2.7)
except NameError:  # CPython 3, used by the host tests
    unicode = str  # noqa: A001

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ut_parse import (  # noqa: E402
    MAX_CASES,
    allow_start as may_start_app,
    cross_check_fail_count,
    is_local_address,
    load_cfg,
    to_status,
    to_text,
    to_uint,
    validate_run,
)
from ut_run import arm_run as run_reset  # noqa: E402

DEFAULT_TARGET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target.txt")
TARGET = os.environ.get("CODESYS_UNITTEST_TARGET") or DEFAULT_TARGET

# Populated by configure(). Kept out of import so the host test suite can
# import this module and drive run_tests() with fake CODESYS objects.
CFG = {}
LOG = u""
RESULT = u""


def write_json(path, obj):
    body = json.dumps(obj, indent=2, sort_keys=True)
    f = codecs.open(path, "w", "utf-8")
    try:
        f.write(body)
    finally:
        f.close()


def log_write(path, msg):
    if not path:
        return
    try:
        f = codecs.open(path, "a", "utf-8")
        try:
            f.write(unicode(msg) + u"\n")
        finally:
            f.close()
    except Exception:
        pass


def configure(target=None):
    """Load target.txt into the module globals (called by main()/tests)."""
    global TARGET, CFG, LOG, RESULT
    if target:
        TARGET = target
    CFG = load_cfg(TARGET)
    LOG = CFG.get(u"log", u"")
    RESULT = CFG.get(u"result", u"")
    return CFG


def resolve_change(default_name=u"Never"):
    name = CFG.get(u"change", default_name) or default_name
    try:
        return getattr(OnlineChangeOption, name), name
    except Exception:
        return getattr(OnlineChangeOption, default_name), default_name


def do_login(oapp):
    """Login with the configured change option ONLY. Never escalate to Force."""
    change, name = resolve_change(u"Never")
    try:
        oapp.login(change, False)
        return True
    except Exception as e:
        log_write(LOG, u"login(%s): %r" % (name, e,))
        return False


def find_app(proj):
    apps = []

    def walk(o, prefix):
        try:
            if getattr(o, u"is_application", False):
                apps.append((prefix, o))
                return
        except Exception:
            pass
        try:
            kids = o.get_children() or []
        except Exception:
            kids = []
        for k in kids:
            try:
                nm = unicode(k.get_name())
            except Exception:
                nm = u"?"
            walk(k, prefix + u"/" + nm if prefix else nm)

    for top in (proj.get_children() or []):
        try:
            nm = unicode(top.get_name())
        except Exception:
            nm = u"?"
        walk(top, nm)
    if not apps:
        try:
            a = proj.active_application
            if a:
                return (u"Application", a)
        except Exception:
            pass
        return (None, None)
    name = CFG.get(u"app", u"")
    if name:
        for full, a in apps:
            if full == name or full.endswith(u"/" + name):
                return (full, a)
            try:
                if unicode(a.get_name()) == name:
                    return (full, a)
            except Exception:
                pass
    return apps[0]


def find_device(proj):
    name = CFG.get(u"device", u"")
    found = []

    def consider(o, nm):
        is_dev = False
        try:
            is_dev = bool(getattr(o, u"is_device", False))
        except Exception:
            is_dev = False
        if (not is_dev) and (u"SoftMotion" in nm or u"Control" in nm or nm == u"Device"):
            is_dev = True
        if is_dev and nm.lower() not in (u"library manager", u"task configuration"):
            if name:
                if nm == name:
                    found.append(o)
            elif not found:
                found.append(o)

    def walk(o):
        if found and name:
            return
        try:
            kids = o.get_children() or []
        except Exception:
            kids = []
        for k in kids:
            try:
                nm = unicode(k.get_name())
            except Exception:
                nm = u"?"
            consider(k, nm)
            if not (found and name):
                walk(k)

    for top in (proj.get_children() or []):
        try:
            nm = unicode(top.get_name())
        except Exception:
            nm = u"?"
        consider(top, nm)
        if not (found and name):
            walk(top)
    return found[0] if found else None


def ensure_gateway(dev):
    """Configure device communication (local SoftMotion / Control Win).

    Keep in sync with codesys-connect/online_ops.py: filling the communication
    settings object (device_name / device_address / gateway_guid) is the
    preferred path there and is required on some builds. A copy of only the
    set_gateway_* helpers is not enough.
    """
    address = CFG.get(u"address", u"127.0.0.1")
    port = CFG.get(u"port", u"11740")
    gw_name = CFG.get(u"gateway", u"Gateway-1")
    dev_name = CFG.get(u"device_name", u"")
    if not dev_name:
        dev_name = CFG.get(u"device", u"Device")

    cs = None
    try:
        cs = dev.get_device_communication_settings()
        log_write(LOG, u"comm_settings before: device_name=%r address=%r gw=%r" % (
            getattr(cs, u"device_name", u"?"),
            getattr(cs, u"device_address", u"?"),
            getattr(cs, u"gateway_guid", u"?")))
    except Exception as e:
        log_write(LOG, u"comm_settings err=%r" % (e,))

    gateway = None
    try:
        gws = online.gateways
        try:
            found = list(gws.find_with_name(gw_name))
            if found:
                gateway = found[0]
        except Exception as e:
            log_write(LOG, u"find_with_name: %r" % (e,))
        if gateway is None:
            try:
                gateway = gws[0]
            except Exception as e:
                log_write(LOG, u"gws[0]: %r" % (e,))
    except Exception as e:
        log_write(LOG, u"gateways: %r" % (e,))
    log_write(LOG, u"gateway obj=%r" % (gateway,))

    # preferred: fill the communication settings directly
    try:
        if cs is not None:
            try:
                cs.device_name = dev_name
            except Exception as e:
                log_write(LOG, u"cs.device_name: %r" % (e,))
            try:
                if port and port not in address:
                    cs.device_address = u"%s:%s" % (address, port)
                else:
                    cs.device_address = address
            except Exception as e:
                log_write(LOG, u"cs.device_address: %r" % (e,))
            try:
                if gateway is not None:
                    cs.gateway_guid = gateway.guid
            except Exception as e:
                log_write(LOG, u"cs.gateway_guid: %r" % (e,))
            log_write(LOG, u"comm_settings updated name=%s addr=%s" % (
                dev_name, getattr(cs, u"device_address", u"?")))
    except Exception as e:
        log_write(LOG, u"comm_settings write: %r" % (e,))

    # also call set_gateway_* helpers (some builds require them)
    try:
        if gateway is not None:
            try:
                dev.set_gateway_and_ip_address(gateway, address, int(port) if port else 11740)
                log_write(LOG, u"set_gateway_and_ip_address ok")
            except Exception as e:
                log_write(LOG, u"set_gateway_and_ip_address: %r" % (e,))
                try:
                    dev.set_gateway_and_device_name(gateway, dev_name)
                    log_write(LOG, u"set_gateway_and_device_name ok")
                except Exception as e2:
                    log_write(LOG, u"set_gateway_and_device_name: %r" % (e2,))
        else:
            try:
                dev.set_gateway_and_device_name(gw_name, dev_name)
                log_write(LOG, u"set_gateway_and_device_name(string) ok")
            except Exception as e:
                log_write(LOG, u"set_gateway_and_device_name(string): %r" % (e,))
    except Exception as e:
        log_write(LOG, u"WARN set_gateway: %r" % (e,))


def fail(msg, cases=None):
    log_write(LOG, u"FATAL " + msg)
    write_json(RESULT, {"done": False, "error": msg, "cases": cases or []})


def read_credentials():
    """Resolve login from cfg OR the codesys-connect session file.

    Never persist passwords into target.txt: pass user/password via
    CODESYS_UNITTEST_USER / CODESYS_UNITTEST_PASSWORD (or rely on the
    codesys-connect session written by `cc.ps1 connect`).
    """
    user = os.environ.get("CODESYS_UNITTEST_USER") or CFG.get(u"user", u"")
    password = os.environ.get("CODESYS_UNITTEST_PASSWORD") or u""
    if user and password:
        return user, password
    # fall back to codesys-connect session (written by cc.ps1, not by this skill)
    sess = os.path.join(os.path.expanduser(u"~"), u".codesys-connect", u"session.txt")
    if not os.path.isfile(sess):
        return user, password
    try:
        f = codecs.open(sess, u"r", u"utf-8")
        try:
            for line in f:
                line = line.strip()
                if not line or u"=" not in line:
                    continue
                k, v = line.split(u"=", 1)
                k = k.strip().lower()
                if k == u"user" and not user:
                    user = v.strip()
                elif k == u"password" and not password:
                    password = v.strip()
        finally:
            f.close()
    except Exception:
        pass
    return user, password


def run_tests():
    started = time.time()
    log_write(LOG, u"run_tests enter")
    proj_path = CFG.get(u"project", u"")
    if not proj_path or not os.path.isfile(proj_path):
        fail(u"project not found: " + proj_path)
        return
    log_write(LOG, u"opening project %s" % proj_path)
    proj = projects.open(proj_path)
    log_write(LOG, u"project opened")
    app_full, app = find_app(proj)
    dev = find_device(proj)
    log_write(LOG, u"found app=%s dev=%s" % (
        app_full, unicode(dev.get_name()) if dev else None))
    if app is None:
        fail(u"no Application in project")
        return

    user, password = read_credentials()
    if user:
        log_write(LOG, u"set credentials user=%s" % user)
        try:
            online.set_default_credentials(user, password)
        except Exception as e:
            log_write(LOG, u"set_default_credentials: %r" % (e,))

    if dev is not None:
        log_write(LOG, u"ensure_gateway")
        ensure_gateway(dev)

    log_write(LOG, u"connect device")
    try:
        odev = online.create_online_device(dev) if dev is not None else online.create_online_device()
        odev.connect()
    except Exception as e:
        log_write(LOG, u"connect: %r" % (e,))

    log_write(LOG, u"create_online_application")
    try:
        oapp = online.create_online_application(app)
    except Exception as e:
        fail(u"create_online_application: %r" % (e,))
        return

    change = CFG.get(u"change", u"Never") or u"Never"
    log_write(LOG, u"login change=%s" % change)
    if not do_login(oapp):
        fail(u"login failed (change=%s); this runner never downloads. Run "
             u"codesys-connect 'download' when the project changed, then retry." % change)
        return
    log_write(LOG, u"login ok")

    # ensure running so suites advance - but never start a remote target unasked
    is_local = is_local_address(CFG.get(u"address", u"127.0.0.1"))
    start_if_stopped = CFG.get(u"start_if_stopped", u"0").strip().lower() in (
        u"1", u"true", u"yes")
    try:
        st = unicode(oapp.application_state)
        ok_start, why = may_start_app(is_local, start_if_stopped, st)
        st_l = st.lower()
        if st_l in (u"run", u"running"):
            log_write(LOG, u"app already %s" % st)
        elif ok_start:
            oapp.start()
            log_write(LOG, u"started app (was %s)" % st)
        else:
            fail(u"%s on remote target %s; start it on site or pass "
                 u"-StartIfStopped" % (why, CFG.get(u"address", u"?")))
            return
    except Exception as e:
        log_write(LOG, u"start: %r" % (e,))

    log_write(LOG, u"probe GVL_Test protocol")
    try:
        nprobe = oapp.read_value(u"GVL_Test.g_uiCaseCount")
        log_write(LOG, u"GVL_Test present caseCount=%s" % nprobe)
    except Exception as e:
        fail(u"GVL_Test protocol not found in the running application - import "
             u"lib/GVL_Test.st etc. and download the project: %r" % (e,))
        return

    timeout = 60
    try:
        timeout = int(CFG.get(u"timeout_sec", u"60"))
    except Exception:
        timeout = 60

    log_write(LOG, u"arm fresh run")
    reset_err = run_reset(oapp, log=lambda m: log_write(LOG, m))
    if reset_err:
        fail(reset_err)
        return

    log_write(LOG, u"poll g_xDone timeout=%s" % timeout)
    done = False
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            v = oapp.read_value(u"GVL_Test.g_xDone")
            if to_uint(v) == 1:
                done = True
                break
        except Exception as e:
            fail(u"poll GVL_Test.g_xDone: %r" % (e,))
            return
        time.sleep(0.5)
    log_write(LOG, u"poll done=%s" % done)

    if not done:
        detail = u""
        try:
            total = to_uint(oapp.read_value(u"GVL_Test.g_uiSuitesTotal"))
            sdone = to_uint(oapp.read_value(u"GVL_Test.g_uiSuitesDone"))
            detail = u" (suitesDone=%s/%s)" % (sdone, total)
        except Exception:
            pass
        fail(u"timeout waiting for GVL_Test.g_xDone (%ss)%s - check that PRG_Tests is "
             u"assigned to a cyclic task and that the project was downloaded"
             % (timeout, detail))
        return

    out = {
        "done": True,
        "caseCount": 0,
        "failCount": 0,
        "skipCount": 0,
        "durationSec": round(time.time() - started, 3),
        "cases": [],
    }

    try:
        case_count = to_uint(oapp.read_value(u"GVL_Test.g_uiCaseCount"))
        plc_fail = to_uint(oapp.read_value(u"GVL_Test.g_uiFailCount"))
        plc_skip = to_uint(oapp.read_value(u"GVL_Test.g_uiSkipCount"))
        suites_total = to_uint(oapp.read_value(u"GVL_Test.g_uiSuitesTotal"))
        suites_done = to_uint(oapp.read_value(u"GVL_Test.g_uiSuitesDone"))
    except Exception as e:
        fail(u"cannot read GVL_Test counters after g_xDone: %r" % (e,))
        return

    try:
        if to_uint(oapp.read_value(u"GVL_Test.g_xOverflow")) != 0:
            fail(u"more than %d cases were recorded (GVL_Test.g_xOverflow) - raise "
                 u"UT_MAX_CASES and widen g_astCases" % MAX_CASES)
            return
    except Exception:
        pass

    err = validate_run(suites_total, suites_done, case_count, MAX_CASES)
    if err:
        fail(err + u" - check PRG_Tests registration and Begin/Finish")
        return

    for i in range(1, case_count + 1):
        base = u"GVL_Test.g_astCases[%d]" % i
        try:
            name = to_text(oapp.read_value(base + u".sName"))
            status, note = to_status(oapp.read_value(base + u".eStatus"))
            msg = to_text(oapp.read_value(base + u".sMessage"))
        except Exception as e:
            fail(u"cannot read case %d: %r" % (i, e))
            return
        if not name:
            fail(u"case %d has an empty name (caseCount=%s) - results are incomplete"
                 % (i, case_count))
            return
        if note:
            msg = note if not msg else (note + u": " + msg)
        suite = name.split(u".")[0] if u"." in name else u""
        out["cases"].append({
            "sName": name,
            "eStatus": status,
            "sMessage": msg,
            "sSuite": suite,
        })

    computed_fail = len([c for c in out["cases"] if c["eStatus"] == 1])
    computed_skip = len([c for c in out["cases"] if c["eStatus"] == 2])
    xerr = cross_check_fail_count(plc_fail, out["cases"])
    if xerr:
        fail(xerr + u" - results are inconsistent", out["cases"])
        return
    if plc_skip != computed_skip:
        # not fatal (skip bookkeeping can lag), but make it visible
        log_write(LOG, u"WARN skipCount mismatch plc=%s read=%s"
                  % (plc_skip, computed_skip))
        out["warn"] = (u"skipCount mismatch: PLC reports %s, read %s"
                       % (plc_skip, computed_skip))

    out["caseCount"] = len(out["cases"])
    out["failCount"] = computed_fail
    out["skipCount"] = computed_skip
    write_json(RESULT, out)
    log_write(LOG, u"wrote %s cases=%d fail=%d"
              % (RESULT, len(out["cases"]), computed_fail))


def main():
    configure()
    log_write(LOG, u"test_ops start target=%s" % TARGET)
    run_tests()


# Run only when launched by ut.ps1 (which sets CODESYS_UNITTEST_TARGET).
# Importing this module for tests must never execute a run - a leftover
# target.txt next to the script must not be enough to start one.
if os.environ.get(u"CODESYS_UNITTEST_TARGET"):
    try:
        main()
    except Exception:
        try:
            write_json(RESULT, {"error": traceback.format_exc(), "done": False})
        except Exception:
            pass
