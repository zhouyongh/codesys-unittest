# -*- coding: utf-8 -*-
# test_ops.py - codesys-unittest backend (CODESYS --runscript, IronPython 2.7)
# Polls GVL_Test.g_xDone and reads case records into results.json.
#
# target.txt keys (UTF-8):
#   project=<abs .project path>
#   result=<output json path>
#   log=<log file>
#   user= password= device= app= address= port=   (user/password OPTIONAL -
#     prefer env CODESYS_UNITTEST_USER/PASSWORD or the codesys-connect session;
#     never write passwords into target.txt)
#   timeout_sec=60
#   change=Never|Try|Keep|Force   (login only; NEVER auto-escalates to Force)
#
# Output results.json (UTF-8):
#   { "done": true, "caseCount": N, "failCount": N, "skipCount": N,
#     "durationSec": S, "cases": [ {"sName","eStatus","sMessage","sSuite"} ] }

import codecs
import json
import os
import time
import traceback

TARGET = os.environ.get("CODESYS_UNITTEST_TARGET") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "target.txt")


def load_cfg(path):
    cfg = {}
    f = codecs.open(path, "r", "utf-8")
    try:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    finally:
        f.close()
    return cfg


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


CFG = load_cfg(TARGET)
LOG = CFG.get(u"log", u"")
RESULT = CFG.get(u"result", u"")
log_write(LOG, u"test_ops start target=%s" % TARGET)


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
    address = CFG.get(u"address", u"127.0.0.1")
    port = CFG.get(u"port", u"11740")
    gw_name = CFG.get(u"gateway", u"Gateway-1")
    dev_name = CFG.get(u"device_name", u"Device")
    gateway = None
    try:
        gws = online.gateways
        try:
            found = list(gws.find_with_name(gw_name))
            if found:
                gateway = found[0]
        except Exception:
            pass
        if gateway is None:
            try:
                gateway = gws[0]
            except Exception:
                pass
    except Exception as e:
        log_write(LOG, u"gateways: %r" % (e,))
    try:
        if gateway is not None:
            dev.set_gateway_and_ip_address(gateway, address, int(port) if port else 11740)
        else:
            dev.set_gateway_and_device_name(gw_name, dev_name)
    except Exception as e:
        log_write(LOG, u"set_gateway: %r" % (e,))


def to_uint(v):
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
    if v is None:
        return u""
    s = unicode(v)
    if len(s) >= 2 and s[0] == u"'" and s[-1] == u"'":
        s = s[1:-1]
    return s


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
        write_json(RESULT, {"error": u"project not found: " + proj_path, "done": False})
        return
    log_write(LOG, u"opening project %s" % proj_path)
    proj = projects.open(proj_path)
    log_write(LOG, u"project opened")
    app_full, app = find_app(proj)
    dev = find_device(proj)
    log_write(LOG, u"found app=%s dev=%s" % (app_full, unicode(dev.get_name()) if dev else None))
    if app is None:
        write_json(RESULT, {"error": u"no Application in project", "done": False})
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
        write_json(RESULT, {"error": u"create_online_application: %r" % (e,), "done": False})
        return

    log_write(LOG, u"login change=%s" % CFG.get(u"change", u"Never"))
    if not do_login(oapp):
        write_json(RESULT, {
            "error": u"login failed (change=%s); not forcing download" % CFG.get(u"change", u"Never"),
            "done": False})
        return
    log_write(LOG, u"login ok")

    # ensure running so suites advance
    try:
        st = unicode(oapp.application_state).lower()
        if st not in (u"run", u"running"):
            oapp.start()
            log_write(LOG, u"started app (was %s)" % st)
        else:
            log_write(LOG, u"app already %s" % st)
    except Exception as e:
        log_write(LOG, u"start: %r" % (e,))

    timeout = 60
    try:
        timeout = int(CFG.get(u"timeout_sec", u"60"))
    except Exception:
        timeout = 60
    log_write(LOG, u"probe GVL_Test protocol")
    try:
        nprobe = oapp.read_value(u"GVL_Test.g_uiCaseCount")
        log_write(LOG, u"GVL_Test present caseCount=%s" % nprobe)
    except Exception as e:
        log_write(LOG, u"GVL_Test missing: %r" % (e,))
        write_json(RESULT, {
            "done": False,
            "error": u"GVL_Test protocol not found in project (copy lib/GVL_Test.st etc.): %r" % (e,),
            "cases": [],
        })
        return

    # arm a fresh run: pulse g_xReset so suite FB one-shot flags clear,
    # zero the shared counters, clear sticky g_xDone
    log_write(LOG, u"arm fresh run")
    try:
        oapp.set_prepared_value(u"GVL_Test.g_xReset", u"TRUE")
        oapp.write_prepared_values()
        time.sleep(0.3)
        oapp.set_prepared_value(u"GVL_Test.g_xReset", u"FALSE")
        oapp.set_prepared_value(u"GVL_Test.g_xDone", u"FALSE")
        oapp.set_prepared_value(u"GVL_Test.g_uiCaseCount", u"0")
        oapp.set_prepared_value(u"GVL_Test.g_uiFailCount", u"0")
        oapp.set_prepared_value(u"GVL_Test.g_uiSkipCount", u"0")
        oapp.set_prepared_value(u"GVL_Test.g_uiSuitesDone", u"0")
        oapp.write_prepared_values()
    except Exception as e:
        log_write(LOG, u"arm reset: %r" % (e,))

    log_write(LOG, u"poll g_xDone timeout=%s" % timeout)

    done = False
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            v = oapp.read_value(u"GVL_Test.g_xDone")
            log_write(LOG, u"g_xDone=%s" % v)
            if to_uint(v) == 1:
                done = True
                break
        except Exception as e:
            log_write(LOG, u"poll g_xDone: %r" % (e,))
            break
        time.sleep(0.5)
    log_write(LOG, u"poll done=%s" % done)

    out = {
        "done": bool(done),
        "caseCount": 0,
        "failCount": 0,
        "skipCount": 0,
        "durationSec": round(time.time() - started, 3),
        "cases": [],
    }
    if not done:
        out["error"] = u"timeout waiting for GVL_Test.g_xDone (%ss)" % timeout

    try:
        out["caseCount"] = to_uint(oapp.read_value(u"GVL_Test.g_uiCaseCount"))
        out["failCount"] = to_uint(oapp.read_value(u"GVL_Test.g_uiFailCount"))
        out["skipCount"] = to_uint(oapp.read_value(u"GVL_Test.g_uiSkipCount"))
    except Exception as e:
        log_write(LOG, u"read counters: %r" % (e,))

    n = out["caseCount"] or 0
    if n < 0:
        n = 0
    if n > 64:
        n = 64
        log_write(LOG, u"WARN caseCount>64, truncating")
    for i in range(1, n + 1):
        base = u"GVL_Test.g_astCases[%d]" % i
        try:
            name = to_text(oapp.read_value(base + u".sName"))
            st = to_uint(oapp.read_value(base + u".eStatus"))
            msg = to_text(oapp.read_value(base + u".sMessage"))
        except Exception as e:
            log_write(LOG, u"read case %d: %r" % (i, e,))
            continue
        if not name:
            log_write(LOG, u"empty name at index %d, stop" % i)
            break
        suite = name.split(u".")[0] if u"." in name else u""
        out["cases"].append({
            "sName": name,
            "eStatus": st,
            "sMessage": msg,
            "sSuite": suite,
        })

    # keep counters consistent with what we actually read
    out["caseCount"] = len(out["cases"])
    out["failCount"] = len([c for c in out["cases"] if c["eStatus"] == 1])
    out["skipCount"] = len([c for c in out["cases"] if c["eStatus"] == 2])
    if not out.get("done") and not out.get("error"):
        out["error"] = u"timeout waiting for GVL_Test.g_xDone (%ss)" % timeout

    write_json(RESULT, out)
    log_write(LOG, u"wrote %s cases=%d fail=%d" % (RESULT, len(out["cases"]), out["failCount"]))


try:
    run_tests()
except Exception:
    try:
        write_json(RESULT, {"error": traceback.format_exc(), "done": False})
    except Exception:
        pass
