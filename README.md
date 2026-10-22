# codesys-unittest

xunit-style CODESYS unit tests for AI agents. One command, one short report.

Tests are ST function blocks using xunit vocabulary (suite / test / assert / fixture).
A host runner starts SoftMotion / Control Win, logs in via
[codesys-connect](https://github.com/zhouyongh/codesys-connect), polls results, and
emits text + JUnit XML.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ut.ps1 run -Project D:\repo\projects\App.project -UserFile user.txt
powershell -NoProfile -ExecutionPolicy Bypass -File ut.ps1 run -Mock      # wiring check, green
powershell -NoProfile -ExecutionPolicy Bypass -File ut.ps1 run -MockFail  # report check, red
```

| Command | What it does |
|---|---|
| `run` | ensure runtime -> login (Never) -> reset -> run suites -> report. **No download.** |
| `run -Mock` / `run -MockFail` | synthetic green / red run, no PLC |
| `ensure-runtime` / `stop-runtime` | SoftMotion / Control Win lifecycle (resolved install only) |
| `report` | format `results.json` (from `out/`) into text + JUnit |

Real PLC: pass `-Address <ip> -Port <port>` and start the application yourself
(or pass `-StartIfStopped`). The runner never downloads and never force-logs-in;
run codesys-connect `download` first when the logic changed.

## Authoring

Copy the protocol POUs from `lib/` (`GVL_Test`, `UT_Case`, `FB_Assert` + methods,
`PRG_Tests`) into the project's Application node (`src/plc/<project>/Application/...`
in a codesys-sync repo) and keep the `// PATH: Application/...` headers. `F_Clamp` +
`FB_F_Clamp_Test` are the reference feature/suite. Each suite FB =
one `Test_*` method per case; asserts write into `GVL_Test`; the runner polls
`GVL_Test.g_xDone`. Register every suite in `PRG_Tests`, set `g_uiSuitesTotal` to the
number of suites, and assign `PRG_Tests` to a cyclic task.

`examples/sample-app/` is a complete reference: `Application/F_Clamp.st`, the test
POUs, and `structure_ops.txt` for a one-shot codesys-sync import.
`examples/conveyor-loop/` is a four-feature demo (13 methods / 19 cases) with a
red → green → regression walk-through and a two-runs-in-a-row check. Its suites
live in `Application/Tests` with per-case `Setup` / `TearDown`; see
`docs/TEST_STYLE.md`.

Full workflow (feature / regression / report / troubleshooting): see `SKILL.md`.

## Requirements

- Windows, PowerShell 5.1+
- CODESYS 3.5.x with Scripting Engine (SP must match the project)
- [codesys-connect](https://github.com/zhouyongh/codesys-connect) (sibling folder, or `CODESYS_CONNECT_HOME`)
- [codesys-sync](https://github.com/zhouyongh/codesys-sync) (import `lib/`, build)
- Python 3.8+ for `report.py` (`CODESYS_UNITTEST_PYTHON`, legacy `MIMO_PYTHON`, or `python` on PATH)

Credentials live in codesys-connect's session file. Prefer `-UserFile`; this skill
never writes passwords into work files, and `run` no longer creates or updates a
codesys-connect session. `test_ops.py` reads login from env
(`CODESYS_UNITTEST_USER`/`CODESYS_UNITTEST_PASSWORD`) or the codesys-connect session.

Full interface: [SKILL.md](SKILL.md).

## Self-test

The runner has its own unit tests (stdlib `unittest`, no extra packages):

```powershell
python -m unittest discover -s tests -v
```

| Layer | File | Covers |
|---|---|---|
| L0 | `tests/test_protocol.py` | `lib/` constants vs `ut_parse` (64 slots, symbols) |
| L0 | `tests/test_conveyor_sample.py` | demo wiring: protocol copies, suite methods, `structure_ops`, `PRG_Tests` |
| L1 | `tests/test_parse.py` | typed status / uint parsing, cfg, run gates |
| L1 | `tests/test_report.py` | red/green, error paths, JUnit counts, unicode |
| L2 | `tests/test_reset.py` | reset order, hold, release, failure paths (fake IO) |
| L3 | `tests/test_cli.py` | `-Change` gate, `-Mock` / `-MockFail`, `report`, `status` |
| L3 | `tests/test_cli_real.py` | real launch path with a fake runner: target.txt, watchdog, results copy, no password in files |
| L4 | `tests/test_test_ops_run.py` | `run_tests()` with fake projects / online app / GVL |
| L5 | `tests/test_live_smoke.py` | two live runs on a prepared target (skipped by default) |

The CLI tests pass `CODESYS_UNITTEST_PYTHON=sys.executable` to the child, so they
do not depend on a `python` alias on PATH. CI runs the default suite on Windows
(`.github/workflows/self-tests.yml`); L5 is opt-in - see
[docs/LIVE_SMOKE.md](docs/LIVE_SMOKE.md).

`ut.ps1` also has test-only hooks used by L3/L4 (`CODESYS_UNITTEST_EXE`,
`_PROFILE`, `_OPS`, `_WATCHDOG_SEC`); they are documented in the live-smoke
guide, not in the user interface.

Shared helpers live in `ut_parse.py` (pure parsing/policy) and `ut_run.py`
(reset sequence, injectable IO); both are Python 2/3 and used by `test_ops.py`
under IronPython and by the host test suite.
