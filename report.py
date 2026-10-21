# report.py - results.json -> compact text + JUnit XML (codesys-unittest)
# Usage: python report.py <results.json> <out_dir>
# UTF-8 everywhere. No credentials. Safe for CI.
#
# A run is green only when it actually ran: the backend already fails a run
# with zero cases, and this script keeps a pipeline error visible as a failing
# test case so a red run can never look green.

from __future__ import print_function

import json
import os
import sys
import xml.etree.ElementTree as ET

PIPELINE = "pipeline"


def _read_text(path):
    f = open(path, "rb")
    try:
        raw = f.read()
    finally:
        f.close()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8")


def _write_text(path, text):
    f = open(path, "wb")
    try:
        f.write(text.encode("utf-8"))
    finally:
        f.close()


def _out(text):
    """Write UTF-8 regardless of the console code page."""
    data = text.encode("utf-8")
    buf = getattr(sys.stdout, "buffer", None)
    if buf is not None:
        buf.write(data)
        buf.flush()
    else:  # very old Python / redirected object
        sys.stdout.write(text)


def load_results(path):
    return json.loads(_read_text(path))


def _as_int(v, default=1):
    try:
        if v is None:
            return default
        return int(v)
    except Exception:
        return default


def status_of(c):
    """0 = pass, 1 = fail, 2 = skip. Unknown values count as failures."""
    e = _as_int(c.get("eStatus"), 1)
    if e in (0, 1, 2):
        return e
    return 1


def status_word(e):
    if e == 2:
        return "SKIP"
    if e == 1:
        return "FAIL"
    return "PASS"


def collect(results):
    """Return the cases to display, including a synthetic pipeline failure."""
    cases = list(results.get("cases") or [])
    if not results.get("done"):
        msg = results.get("error") or "run did not finish (g_xDone was never set)"
        cases.append({
            "sName": PIPELINE,
            "sSuite": "codesys-unittest",
            "eStatus": 1,
            "sMessage": str(msg),
        })
    elif not cases:
        cases.append({
            "sName": PIPELINE,
            "sSuite": "codesys-unittest",
            "eStatus": 1,
            "sMessage": "no test cases were recorded (PRG_Tests not running or no suite registered?)",
        })
    return cases


def write_text(path, results):
    cases = collect(results)
    failed = [c for c in cases if status_of(c) == 1]
    skipped = [c for c in cases if status_of(c) == 2]
    lines = []
    if results.get("error") and not results.get("done"):
        lines.append("ERR %s" % results.get("error"))
    lines.append("CODESYS unit tests - %d case%s, %d failed, %d skipped" % (
        len(cases), "" if len(cases) == 1 else "s", len(failed), len(skipped)))
    for c in cases:
        st = status_word(status_of(c))
        msg = c.get("sMessage") or ""
        name = c.get("sName") or "?"
        if msg:
            lines.append("%s  %s  %s" % (st, name, msg))
        else:
            lines.append("%s  %s" % (st, name))
    body = u"\n".join(lines) + u"\n"
    _write_text(path, body)
    return body


def write_junit(path, results):
    cases = collect(results)
    n_fail = len([c for c in cases if status_of(c) == 1])
    n_skip = len([c for c in cases if status_of(c) == 2])
    suite = ET.Element("testsuite", {
        "name": results.get("suiteName") or "codesys-unittest",
        "tests": str(len(cases)),
        "failures": str(n_fail),
        "errors": "0",
        "skipped": str(n_skip),
        "time": str(results.get("durationSec") or 0),
    })
    for c in cases:
        tc = ET.SubElement(suite, "testcase", {
            "classname": c.get("sSuite") or "PLC",
            "name": c.get("sName") or "?",
            "time": "0",
        })
        st = status_of(c)
        if st == 1:
            fail = ET.SubElement(tc, "failure", {
                "message": c.get("sMessage") or "failed",
                "type": "PipelineError" if (c.get("sName") == PIPELINE) else "AssertionError",
            })
            fail.text = c.get("sMessage") or "failed"
        elif st == 2:
            ET.SubElement(tc, "skipped", {
                "message": c.get("sMessage") or "skipped",
            })
    tree = ET.ElementTree(suite)
    try:
        ET.indent(tree, space="  ")  # Python 3.9+
    except Exception:
        pass
    xml_body = ET.tostring(suite, encoding="utf-8", xml_declaration=True)
    f = open(path, "wb")
    try:
        f.write(xml_body)
    finally:
        f.close()
    return (len(cases), n_fail, n_skip)


def main(argv):
    if len(argv) < 3:
        _out("ERR usage: report.py <results.json> <out_dir>\n")
        return 2
    res_path, out_dir = argv[1], argv[2]
    if not os.path.isfile(res_path):
        _out("ERR results not found: %s\n" % res_path)
        return 1
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    try:
        results = load_results(res_path)
    except Exception as e:
        _out("ERR cannot read %s: %s\n" % (res_path, e))
        return 1

    txt_path = os.path.join(out_dir, "report.txt")
    xml_path = os.path.join(out_dir, "junit.xml")
    body = write_text(txt_path, results)
    write_junit(xml_path, results)
    _out(body)
    _out("JUnit: %s\n" % xml_path)

    if results.get("error") and not results.get("done"):
        return 1
    for c in collect(results):
        if status_of(c) == 1:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
