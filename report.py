# report.py - results.json -> compact text + JUnit XML (codesys-unittest)
# Usage: python report.py <results.json> <out_dir>
# UTF-8 everywhere. No credentials. Safe for CI.

from __future__ import print_function

import json
import os
import sys
import xml.etree.ElementTree as ET


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


def load_results(path):
    return json.loads(_read_text(path))


def status_word(e):
    try:
        e = int(e)
    except Exception:
        e = 0
    if e == 2:
        return "SKIP"
    if e == 1:
        return "FAIL"
    return "PASS"


def _as_int(v, default=0):
    try:
        if v is None:
            return default
        return int(v)
    except Exception:
        return default


def write_text(path, results):
    cases = results.get("cases") or []
    failed = [c for c in cases if _as_int(c.get("eStatus")) == 1]
    skipped = [c for c in cases if _as_int(c.get("eStatus")) == 2]
    lines = []
    if results.get("error") and not results.get("done"):
        lines.append("ERR %s" % results.get("error"))
    lines.append("CODESYS unit tests - %d cases, %d failed, %d skipped" % (
        len(cases), len(failed), len(skipped)))
    for c in cases:
        st = status_word(c.get("eStatus", 0))
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
    cases = results.get("cases") or []
    n_fail = len([c for c in cases if _as_int(c.get("eStatus")) == 1])
    n_skip = len([c for c in cases if _as_int(c.get("eStatus")) == 2])
    suite = ET.Element("testsuite", {
        "name": results.get("suiteName") or "codesys-unittest",
        "tests": str(len(cases)),
        "failures": str(n_fail),
        "skipped": str(n_skip),
        "time": str(results.get("durationSec") or 0),
    })
    if results.get("error") and not results.get("done"):
        # surface the pipeline error as a single failing case so CI notices
        tc = ET.SubElement(suite, "testcase", {
            "classname": "codesys-unittest",
            "name": "pipeline",
            "time": "0",
        })
        fail = ET.SubElement(tc, "failure", {
            "message": str(results.get("error")),
            "type": "PipelineError",
        })
        fail.text = str(results.get("error"))
    for c in cases:
        tc = ET.SubElement(suite, "testcase", {
            "classname": c.get("sSuite") or "PLC",
            "name": c.get("sName") or "?",
            "time": "0",
        })
        st = _as_int(c.get("eStatus"))
        if st == 1:
            fail = ET.SubElement(tc, "failure", {
                "message": c.get("sMessage") or "failed",
                "type": "AssertionError",
            })
            fail.text = c.get("sMessage") or "failed"
        elif st == 2:
            ET.SubElement(tc, "skipped", {
                "message": c.get("sMessage") or "skipped",
            })
    tree = ET.ElementTree(suite)
    try:
        ET.indent(tree, space="  ")
    except Exception:
        pass
    # write XML as UTF-8 with declaration
    xml_body = ET.tostring(suite, encoding="utf-8", xml_declaration=True)
    f = open(path, "wb")
    try:
        f.write(xml_body)
    finally:
        f.close()


def main(argv):
    if len(argv) < 3:
        print("ERR usage: report.py <results.json> <out_dir>")
        return 2
    res_path, out_dir = argv[1], argv[2]
    if not os.path.isfile(res_path):
        print("ERR results not found: %s" % res_path)
        return 1
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    results = load_results(res_path)
    txt_path = os.path.join(out_dir, "report.txt")
    xml_path = os.path.join(out_dir, "junit.xml")
    body = write_text(txt_path, results)
    write_junit(xml_path, results)
    sys.stdout.write(body)
    print("JUnit: %s" % xml_path)
    if results.get("error") and not results.get("done"):
        return 1
    n_fail = _as_int(results.get("failCount"), -1)
    if n_fail < 0:
        cases = results.get("cases") or []
        n_fail = len([c for c in cases if _as_int(c.get("eStatus")) == 1])
    return 1 if n_fail > 0 else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
