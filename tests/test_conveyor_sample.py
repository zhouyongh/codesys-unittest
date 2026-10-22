# test_conveyor_sample.py - L0: the conveyor-loop sample must stay wired up.
# Run: python -m unittest discover -s tests -v
#
# No CODESYS needed: checks the protocol copies (ignoring the PATH line), the
# Tests/ folder, suite/method wiring, Setup/TearDown, structure_ops and the
# PRG_Tests registry.

import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = os.path.join(ROOT, "examples", "conveyor-loop")
APP = os.path.join(SAMPLE, "Application")
TESTS = os.path.join(SAMPLE, "Tests")
LIB = os.path.join(ROOT, "lib")

SUITES = (
    "FB_DecideSort_Test",
    "FB_Diverter_Test",
    "FB_Conveyor_Test",
    "FB_Stats_Test",
)


def _read(path):
    f = open(path, "rb")
    try:
        raw = f.read()
    finally:
        f.close()
    return raw.decode("utf-8-sig")


def _body(path):
    """Protocol text without the leading // PATH line (paths differ per copy)."""
    lines = _read(path).split("\n")
    if lines and lines[0].startswith("// PATH:"):
        lines = lines[1:]
    return "\n".join(lines).rstrip("\n")


def _st_files(base):
    out = []
    for dirpath, _dirnames, filenames in os.walk(base):
        for name in filenames:
            if name.endswith(".st"):
                out.append(os.path.join(dirpath, name))
    return out


class TestProtocolCopies(unittest.TestCase):
    def test_protocol_matches_lib(self):
        rels = ["GVL_Test.st", "UT_Case.st", "FB_Assert.st"]
        for name in os.listdir(os.path.join(LIB, "FB_Assert")):
            if name.endswith(".st"):
                rels.append(os.path.join("FB_Assert", name))
        for rel in rels:
            with self.subTest(rel=rel):
                self.assertEqual(
                    _body(os.path.join(TESTS, rel)),
                    _body(os.path.join(LIB, rel)),
                    "sample copy drifted from lib/: " + rel,
                )


class TestSuiteWiring(unittest.TestCase):
    def test_each_suite_calls_exactly_its_methods(self):
        for suite in SUITES:
            with self.subTest(suite=suite):
                body = _read(os.path.join(TESTS, suite + ".st"))
                self.assertIn("// ===== TEST SUITE =====", body)
                self.assertIn("FUNCTION_BLOCK " + suite, body)
                called = set(re.findall(r"(\w+)\(\);", body))
                called.discard("Finish")  # ass.Finish() is suite lifetime
                method_dir = os.path.join(TESTS, suite)
                files = set(
                    name[:-3] for name in os.listdir(method_dir)
                    if name.endswith(".st")
                )
                self.assertEqual(called, files,
                                 "%s: call/file mismatch" % suite)

    def test_each_method_has_case_header_and_public_method(self):
        for suite in SUITES:
            for name in os.listdir(os.path.join(TESTS, suite)):
                if not name.endswith(".st"):
                    continue
                method = name[:-3]
                text = _read(os.path.join(TESTS, suite, name))
                self.assertIn("// ===== TEST CASE =====", text, name)
                self.assertIn("METHOD PUBLIC " + method, text, name)
                self.assertTrue(
                    text.startswith(
                        "// PATH: Application/Tests/%s/%s" % (suite, method)),
                    name,
                )

    def test_prg_tests_registers_the_selected_suites(self):
        text = _read(os.path.join(TESTS, "PRG_Tests.st"))
        self.assertIn("g_uiSuitesTotal", text)
        self.assertIn("g_sFilter", text)
        for suite in SUITES:
            self.assertIn(suite, text, suite)
        self.assertEqual(len(re.findall(r"fb\w+\(\);", text)), 4)
        self.assertNotIn("xAllFinished", text)


class TestStructureOps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = _read(os.path.join(SAMPLE, "structure_ops.txt"))
        cls.ops = []
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            parts = [p.strip() for p in s.split("|")]
            cls.ops.append((parts[0].upper(), parts[1:]))

    def _args(self, op):
        return [args for name, args in self.ops if name == op]

    def test_tests_folder_is_created(self):
        folders = {(args[0], args[1]) for args in self._args("CREATE_FOLDER")}
        self.assertIn(("Application", "Tests"), folders)

    def test_task_path_is_spaced_and_points_at_prg(self):
        assigns = self._args("ASSIGN_TO_TASK")
        self.assertEqual(len(assigns), 1)
        task, prog = assigns[0]
        self.assertEqual(task, "Application/Task Configuration/MainTask")
        self.assertEqual(prog, "Application/Tests/PRG_Tests")

    def test_every_method_is_created(self):
        created = {(args[0], args[1]) for args in self._args("CREATE_METHOD")}
        for suite in SUITES:
            method_dir = os.path.join(TESTS, suite)
            for name in os.listdir(method_dir):
                if name.endswith(".st"):
                    key = ("Application/Tests/" + suite, name[:-3])
                    self.assertIn(key, created, "%s/%s" % key)

    def test_features_and_suite_fbs_are_created(self):
        fbs = {args[1] for args in self._args("CREATE_FB")}
        for name in SUITES:
            self.assertIn(name, fbs)
        for name in ("FB_Assert", "FB_Diverter", "FB_Conveyor", "FB_Stats"):
            self.assertIn(name, fbs)
        self.assertIn(["Application", "F_DecideSort", "BOOL"],
                      self._args("CREATE_FUN"))


class TestHeadersAndSize(unittest.TestCase):
    def test_all_st_files_have_path_and_markers(self):
        for path in _st_files(SAMPLE):
            rel = os.path.relpath(path, SAMPLE).replace("\\", "/")
            text = _read(path)
            self.assertTrue(text.startswith("// PATH: Application/"),
                            "missing PATH header: " + rel)
            self.assertIn("// ===== DECLARATION =====", text, rel)
            self.assertIn("// ===== IMPLEMENTATION =====", text, rel)
            self.assertNotIn("<Application>", text, rel)

    def test_sample_size_matches_the_docs(self):
        methods = []
        asserts = 0
        for suite in SUITES:
            for name in os.listdir(os.path.join(TESTS, suite)):
                if not name.endswith(".st"):
                    continue
                if name.startswith("Test_"):
                    methods.append(name[:-3])
                asserts += len(re.findall(
                    r"ass\.Assert", _read(os.path.join(TESTS, suite, name))))
        self.assertEqual(len(methods), 13)
        self.assertEqual(asserts, 19)


if __name__ == "__main__":
    unittest.main()
