---
name: codesys-unittest
description: CODESYS unit tests for AI agents - xunit-style ST suites (suite / test / assert / fixture) compiled into the PLC and executed in-cycle on SoftMotion / Control Win or a real target, with a host runner that starts the runtime, logs in via codesys-connect with change=Never (never downloads), polls GVL_Test and emits a text report plus JUnit XML. Use when the user wants PLC unit tests, CODESYS unit test, codesys-unittest, PLC 测试 / 单元测试 / 回归测试 / 测试用例 / 写测试 / 红绿, or a testable feature workflow (write tests, run tests, regression gate). Not for reading/writing PLC variables (codesys-connect) or project import/export (codesys-sync).
---

# codesys-unittest - xunit-style CODESYS unit tests

Tests are ST function blocks using **xunit vocabulary** (suite / test / assert / fixture).
They are compiled into the application and assert **inside the PLC cycle**; the host
only starts the runtime, logs in, polls `GVL_Test`, and formats the report.

One command -> one short result. No MCP JSON dumps.

## Prerequisites

| Need | Role | Notes |
|---|---|---|
| Windows + PowerShell 5.1+ | runner | `ut.ps1` / `common.ps1` |
| CODESYS 3.5.x with Scripting Engine | compile + run | SP must match the project (see Version pinning) |
| [codesys-connect](../codesys-connect/SKILL.md) | online channel, install resolution | sibling folder or `CODESYS_CONNECT_HOME`; **required** |
| [codesys-sync](../codesys-sync/SKILL.md) | import `lib/`, build the project | needed for the repo workflow |
| Python 3.8+ | `report.py` (text + JUnit) | `CODESYS_UNITTEST_PYTHON`, legacy `MIMO_PYTHON`, or `python` on PATH |
| Project closed in the IDE | login/build | same rule as codesys-connect |

## The two-step loop (read this)

`ut.ps1 run` **never downloads**: it logs in with `change=Never` and only reads what is
already running. Load new logic explicitly first:

```powershell
# 1) logic changed? import + download explicitly (codesys-sync / codesys-connect)
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-sync>\import.ps1 -Root <repo> -Sync -VerifyBuild
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-connect>\cc.ps1 connect -Project <abs .project> -UserFile <user.txt>
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-connect>\cc.ps1 download
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-connect>\cc.ps1 start

# 2) run the tests (never downloads, never forces)
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-unittest>\ut.ps1 run `
    -Project <abs .project> -UserFile <user.txt>
```

The runner does **not** call codesys-connect `connect`: that would login with its
default `change=Try` (possible online change) and persist a session file. Credentials
come from `-UserFile`, env, or an already existing codesys-connect session.

## Interface

```powershell
ut.ps1 run -Project <abs .project> [-UserFile f | -User u] [-Address 127.0.0.1] [-Port 11740]
ut.ps1 ensure-runtime [-SoftMotion] [-MaxAgeHours 2]
ut.ps1 stop-runtime
ut.ps1 status
ut.ps1 report [-Project <abs .project>] [-Results <results.json>] [-OutDir dir]
ut.ps1 run -Mock        # green synthetic run - wiring check, no PLC
ut.ps1 run -MockFail    # red synthetic run - report/JUnit check
```

| Command | Meaning | Output |
|---|---|---|
| `run` | ensure runtime -> login (Never) -> reset -> poll -> report. **No download.** | summary + report paths |
| `run -Mock` | synthetic all-green results | summary + report paths, exit 0 |
| `run -MockFail` | synthetic result with one failure | summary + report paths, exit 1 |
| `ensure-runtime` | start SoftMotion/Control Win if needed; verify port | `OK runtime=1 pid=... port=11740` |
| `stop-runtime` | stop the soft PLC (resolved install first, all as fallback) | `OK runtime=0` |
| `status` | runtime pid + port reachability | `runtime_pid=... port_open=...` |
| `report` | format an existing `results.json` into text + JUnit | summary + report paths |

Exit code 0 only when the run really executed and passed: **zero cases, a missing
`GVL_Test`, an ineffective reset, a timeout, or any failed assert all exit 1.**

## Parameters

| Flag | Meaning |
|---|---|
| `-Project` | Absolute `.project` path (required for a real `run`) |
| `-UserFile` | Credentials file (preferred - keeps the password off the command line) |
| `-User` / `-Password` | Target login (password via env `CODESYS_UNITTEST_PASSWORD`; prefer `-UserFile`) |
| `-Address` / `-Port` | Target (default `127.0.0.1:11740`) |
| `-Change` | Login option, default `Never`. Only `Never` or `Keep` are accepted; `Force`/`Try` are rejected (they download or online-change). |
| `-StartIfStopped` | Allow starting a **remote** application that is not RUN (default: local only) |
| `-Device` / `-App` | Device / application node names |
| `-TimeoutSec` | Poll timeout for `g_xDone` (default 60; watchdog = timeout + 45s) |
| `-MaxAgeHours` | Restart the local runtime when older than this demo-license window (0 = never) |
| `-OutDir` | Report directory (default `out/` beside the project) |
| `-Results` | `report` only: explicit `results.json` (default: `<OutDir>/results.json`, then the work dir) |
| `-Mock` / `-MockFail` | Synthetic results - exercises runner + report only |
| `-CodesysConnect` | Path to codesys-connect (default: sibling `..\codesys-connect`) |
| `-CodesysExe` / `-CodesysProfile` / `-ProjectInfo` | Pin the CODESYS install / profile / export sidecar |

Passwords are never written to files by this skill. Prefer `-UserFile`.

## Test authoring (xunit vocabulary)

Copy the protocol files (`GVL_Test`, `UT_Case`, `FB_Assert` + methods, `PRG_Tests`)
into the project's Application node; `F_Clamp` + `FB_F_Clamp_Test` are the reference
feature/suite (see `examples/sample-app/structure_ops.txt`):

| File | Role |
|---|---|
| `lib/GVL_Test.st` | Result protocol: counters, `g_xDone`, `g_xReset`, case records |
| `lib/FB_Assert.st` | `AssertEquals_BOOL/DINT/LREAL`, `AssertTrue/False`, `Skip` |
| `lib/PRG_Tests.st` | Suite registry + `g_uiSuitesTotal` |
| `lib/FB_Sample_Test.st` | Minimal suite showing fixture / test / assert (not registered) |
| `lib/FB_F_Clamp_Test.st` + `FB_F_Clamp_Test/` | Reference suite, 5 cases |
| `lib/F_Clamp.st` | The feature under test used by the reference suite |

A larger demo - four features, 13 methods / 19 cases, with a red → green →
regression → two-run walk-through - is in `examples/conveyor-loop/`.

Conventions:

- Suite = one `FUNCTION_BLOCK FB_<Feature>_Test`; a `Test_*` method groups the
  assertions for one behaviour. Each `ass.Assert*` records one case, so a method
  with several assertions contributes several cases (the conveyor-loop demo does
  this on purpose).
- Assert name is `Suite.Test_name` - the first segment becomes the JUnit classname.
- Fixture = `VAR` init on the suite; call `ass.Begin('<Suite>')` once per cycle and
  `ass.Finish()` at the end. `Begin` returns FALSE after the suite finished or while
  `g_xReset` is TRUE, so cases are recorded exactly once per run.
- Assertions must not use `0` as the expected value: an unimplemented function often
  returns `0` and would pass.
- ST methods return with `Method := FALSE; RETURN;` - never `RETURN FALSE` (C189).
- `PRG_Tests` **must be assigned to a cyclic task** and must call every registered suite;
  `g_uiSuitesTotal` must match the number of `Finish()` calls per run. The task must
  also run faster than the 1 s reset hold, otherwise a stale suite never restarts.

Feature workflow:

1. Write `FB_Feature_Test` with the cases you want (happy path, boundary, guard).
2. Register it in `PRG_Tests` (`g_uiSuitesTotal` += 1).
3. Download, then `ut.ps1 run` - red is expected.
4. Implement until green; keep the suite as regression.

## Results protocol (online-readable)

`GVL_Test` is the single source of truth. The runner polls `g_xDone`, then reads:

```
g_uiCaseCount, g_uiFailCount, g_uiSkipCount, g_uiSuitesTotal, g_uiSuitesDone, g_xOverflow
g_astCases[i].sName, .eStatus (0=pass 1=fail 2=skip), .sMessage
```

Capacity is 64 cases (`UT_MAX_CASES` / `ARRAY[1..64]`). Overflow sets `g_xOverflow`
and fails the run instead of silently dropping assertions. Older `GVL_Test` builds
without `g_xOverflow` still work: the runner then relies on `caseCount > MAX_CASES`
alone, and that catch is less precise.

A run is green only when: the reset read back as `g_xDone=FALSE, caseCount=0`; every
registered suite finished (`suitesDone == suitesTotal`); at least one case exists; and
the PLC fail counter matches the records that were read.

## Report shape

Text (`stdout` + `<OutDir>/report.txt`):

```
CODESYS unit tests - 3 cases, 1 failed, 1 skipped
PASS  Sample.Test_add
FAIL  Sample.Test_divZeroGuard  expected TRUE
SKIP  Sample.Test_slow  not on this target
JUnit: .../out/junit.xml
```

`<OutDir>/junit.xml` - standard `<testsuite>/<testcase>/<failure>/<skipped>`; the
`tests` / `failures` / `skipped` counters match the emitted nodes, and a pipeline
error is emitted as a failing `pipeline` test case.

`<OutDir>/results.json` is copied from the work directory so `ut.ps1 report` works
per project.

## Runtime lifecycle and safety

- `ensure-runtime` only manages the `CODESYSControlService.exe` of the resolved
  install; runtimes from other installs are left alone.
- It restarts an aged local runtime (demo license ~2h, `-MaxAgeHours 0` disables).
- `run` starts a stopped application **only** for a local target, or on a remote
  target when `-StartIfStopped` is given. It never stops a remote runtime.
- On timeout only the process tree of this run is killed (`taskkill /T`); the user's
  IDE is never touched.
- Login `change=Never`; there is no `Force` path in this skill.

## Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `ERR login failed (change=Never)` | project not downloaded, or device mismatch | run codesys-connect `download`; check DeviceID (`4102/0000 0004` for SoftMotion Win x64) |
| `ERR GVL_Test protocol not found` | `lib/` not imported or not downloaded | import `lib/GVL_Test.st` (+ `UT_Case`), download |
| `ERR timeout waiting for g_xDone (suitesDone=0/1)` | `PRG_Tests` not on a cyclic task, or a suite not called | assign the task, check `g_uiSuitesTotal` |
| `ERR g_xDone fired after 0 of 1 suites` | `g_uiSuitesTotal` is stale/wrong | fix the count in `PRG_Tests` |
| `ERR no test cases recorded` | suite body never reached `Begin`/asserts | check the suite body and reset flag |
| `ERR failCount mismatch` | two suites clearing the shared GVL | never clear `GVL_Test` from a suite |
| `ERR no results.json` | CODESYS crashed / script not found | read `%USERPROFILE%\.codesys-unittest\work-*\ut_log.txt` |
| Chinese text garbled in the console | console code page | `report.txt` is always UTF-8; the runner sets `PYTHONIOENCODING` |

## Pitfalls

- SoftMotion **Win x64** DeviceID is `4102/0000 0004`; the project device must match
  the runtime or login fails. Same rule as codesys-connect.
- `.st` files must keep `// ===== DECLARATION =====` and `// ===== IMPLEMENTATION =====`
  (codesys-sync skips a file without them). `TYPE` declarations are standalone DUTs,
  never inside a GVL.
- Keep tests pure (no wall-clock, no external I/O) so they behave the same on
  simulation and on a real PLC. Hardware cases go into a separate suite and `Skip`.
- Test POUs are compiled into the application: keep `PRG_Tests` out of the production
  task, and remember `GVL_Test` costs ~13 KB (64 x ~200 B).
- `change=Never` proves you are online, not that the **running build** matches the
  `.project`. A stale download can still produce old (green) results - download
  before a regression run.
- Do not commit credentials or `out/`. Session lives in `%USERPROFILE%\.codesys-connect\`.
- All text I/O is UTF-8. Do not rewrite files as ASCII.

## When not to use

- Pure algorithm checks without a runtime -> offline compiler / Matiec.
- Load, performance, or HIL tests -> dedicated tooling.
- Just reading/writing PLC variables -> codesys-connect.
- Project import/export/build -> codesys-sync.

## Files

| File | Role |
|---|---|
| `ut.ps1` | CLI entry |
| `common.ps1` | runtime lifecycle + install/session helpers |
| `test_ops.py` | CODESYS Scripting backend (reset, poll, read results) - IronPython 2.7 |
| `ut_parse.py` | pure parsing / policy helpers (Python 2/3) |
| `ut_run.py` | reset/arm sequence with injectable IO (Python 2/3) |
| `report.py` | results.json -> text + JUnit XML (Python 3.8+) |
| `tests/` | self-tests (stdlib unittest; run with `python -m unittest discover -s tests -v`) |
| `lib/*.st` | test protocol + reference suite to copy into the PLC project |
| `docs/ENGINEERING.md` | feature / regression / report / agent-prompt workflow |
| `examples/sample-app/` | minimal feature + suite + `structure_ops.txt` |
| `examples/conveyor-loop/` | 4-feature demo (13 methods, 19 cases) + closed-loop walk-through |

## Version pinning

Match the project's last-saved compiler version (same rule as codesys-connect).
Pass `-CodesysExe` / `-ProjectInfo` when auto-detect warns.
