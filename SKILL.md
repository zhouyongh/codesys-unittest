---
name: codesys-unittest
description: CODESYS unit-test skill for AI - xunit-style ST test suites on a soft PLC or real target, with host-side runner, SoftMotion/Control Win lifecycle, and JUnit/text reports. Use when the user wants to write or run PLC unit tests, CODESYS unit test, codesys-unittest, SoftMotion test, 回归测试, 单元测试, or a testable feature workflow (write tests, run tests, regression, report).
---

# codesys-unittest - xunit-style CODESYS unit tests

Run unit tests on a CODESYS soft PLC (SoftMotion Win / Control Win) or a real target.
Tests are ST function blocks using **xunit vocabulary** (suite / test / assert / fixture).
A host runner starts the runtime, logs in via **codesys-connect**, polls results, and
emits a compact text report plus JUnit XML.

One command -> one short result. No MCP JSON dumps.

## Why this shape

| Choice | Reason |
|---|---|
| xunit vocabulary, no framework install | AI writes uniformly structured tests; no library/license on the PLC |
| Tests run **inside** the PLC | Deterministic cycle timing; assertions see real motion/FB state |
| Host runner + codesys-connect | Same online path as production download/read/write |
| Text + JUnit XML out | Humans and CI both consume it |

Not used as the main path: host-only pytest, Matiec offline (no runtime),
paid 3S Test Manager.

## Interface

```powershell
# full pipeline: ensure runtime -> connect -> run -> report
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-unittest>\ut.ps1 run `
    -Project <abs .project> [-User u -Password p] [-Address 127.0.0.1] [-Port 11740]

# runtime only (SoftMotion / Control Win)
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-unittest>\ut.ps1 ensure-runtime
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-unittest>\ut.ps1 stop-runtime

# report only (from last run results)
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-unittest>\ut.ps1 report

# dry-run the pipeline with synthetic results (no PLC needed)
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-unittest>\ut.ps1 run -Mock
```

| Command | Meaning | Output |
|---|---|---|
| `ensure-runtime` | Start SoftMotion/Control Win if needed; verify port | `OK runtime=1 pid=... port=11740` |
| `stop-runtime` | Stop the soft PLC | `OK runtime=0` |
| `status` | Runtime pid + port reachability | `runtime_pid=... port_open=...` |
| `run` | ensure -> connect -> download/start tests -> poll -> report | summary + report paths |
| `run -Mock` | Same pipeline, synthetic results (for wiring checks) | summary + report paths |
| `report` | Format `results.json` into text + JUnit XML | summary + report paths |

Exit code 0 when all tests passed; 1 on any failure or `ERR` line.

Real PLC: pass `-Address <ip> -Port <port>`. The runner does **not** start/stop a
remote runtime - it only checks the port is reachable.

## Test authoring (xunit vocabulary)

Drop these into the PLC project (see `lib/`):

| File | Role |
|---|---|
| `lib/GVL_Test.st` | Result protocol: counters + case records the runner reads online |
| `lib/FB_Assert.st` | `AssertEquals_BOOL/DINT/LREAL`, `AssertTrue/False`, `Skip` - append to GVL_Test |
| `lib/PRG_Tests.st` | Suite registry + `GVL_Test.g_xDone` when finished |
| `lib/FB_Sample_Test.st` | Minimal suite showing fixture / test / assert |

Convention:

- Suite = one FUNCTION_BLOCK with `Test_*` methods (each method = one case).
- Fixture = `VAR` init / `Setup` / `Teardown` on the suite FB.
- Assert helpers write `name / status / message` into `GVL_Test`.
- `PRG_Tests` calls every suite each cycle, then sets `g_xDone` when all are finished.

Feature workflow (write a feature):

1. Write `FB_Feature_Test` with the cases you want (`Test_happyPath`, `Test_edgeMin`, ...).
2. Register it in `PRG_Tests`.
3. `ut.ps1 run` - red is expected; fix the feature until green.
4. Keep the suite; it becomes regression.

Regression workflow:

1. Full project download with all suites registered.
2. `ut.ps1 run` - same command every time.
3. JUnit XML for CI, text for humans. Non-zero exit blocks the merge.

## Results protocol (online-readable)

`GVL_Test` is the single source of truth. The runner polls `g_xDone`, then reads:

```
g_uiCaseCount, g_uiFailCount
g_astCases[i].sName, .eStatus (0=pass 1=fail 2=skip), .sMessage
```

This is deliberately simple - no library dependency. Optional later: map CoUnit
results into the same GVL shape.

## Report shape

Text (stdout + `report.txt`):

```
CODESYS unit tests - 3 cases, 1 failed
PASS  Sample.Test_add
FAIL  Sample.Test_divZero  expected no error, got div-by-zero
SKIP  Sample.Test_slow
JUnit: out/junit.xml
```

JUnit XML (`out/junit.xml`) - standard `<testsuite>` / `<testcase>` / `<failure>`.

## Runtime lifecycle

SoftMotion Win / Control Win is a Windows process. `ensure-runtime` will:

1. Find `CODESYSControlService.exe` via install scan / env `CODESYS_UNITTEST_RTS_EXE`.
2. Start `-d CODESYSSoftMotion.cfg` (or `-d CODESYSControl.cfg`) if the port is down.
3. Poll TCP `address:port` (default `127.0.0.1:11740`) up to ~30s.
4. If the process is older than the demo-license window (~2h), restart it.

Real PLC: skip `ensure-runtime`, pass `-Address` / `-Port` to `run`.

## Parameters

| Flag | Meaning |
|---|---|
| `-Project` | Absolute `.project` path (required for a real `run`) |
| `-UserFile` | Credentials file (preferred - keeps the password off the command line) |
| `-User` | Target login username (password via `CODESYS_UNITTEST_PASSWORD` or UserFile) |
| `-Address` / `-Port` | Target (default `127.0.0.1:11740`) |
| `-Device` / `-App` | Device / application node names |
| `-Mock` | Synthetic results - exercises runner + report only |
| `-TimeoutSec` | Poll timeout for `g_xDone` (default 60) |
| `-OutDir` | Report directory (default `out/` beside the project) |
| `-CodesysConnect` | Path to codesys-connect (default: sibling `..\codesys-connect`) |
| `-CodesysProfile` | Pin a CODESYS profile name |

Passwords are **never** written to files by this skill. Login comes from
`-UserFile`, env `CODESYS_UNITTEST_USER`/`CODESYS_UNITTEST_PASSWORD`, or the
codesys-connect session. Prefer `-UserFile`.

## Files

| File | Role |
|---|---|
| `ut.ps1` | CLI entry |
| `common.ps1` | runtime lifecycle + session + invoke helpers |
| `test_ops.py` | CODESYS Scripting backend (poll + read results) |
| `report.py` | results.json -> text + JUnit XML |
| `lib/*.st` | test protocol templates to copy into the PLC project |
| `docs/ENGINEERING.md` | feature / regression / report / agent-prompt workflow |
| `examples/sample-app/` | minimal feature + suite (F_Clamp) |

## Workflow docs

See `docs/ENGINEERING.md` for: how to write tests with a feature, how regression
runs, what the report looks like, and the agent prompt shape. See
`examples/sample-app/` for a copy-paste feature + suite.

## Pitfalls

- SoftMotion **Win x64** DeviceID is `4102/0000 0004`; the project device must match
  or login fails. Same rule as codesys-connect.
- Demo runtime license is ~2 hours. `ensure-runtime` restarts an aged process.
- Keep tests pure where possible (no wall-clock, no external I/O) so they are
  deterministic on both simulation and a real PLC.
- Do not commit credentials. Session lives in `%USERPROFILE%\.codesys-connect\`.
- All text I/O is UTF-8. Do not rewrite files as ASCII.

## Version pinning

Same rule as codesys-connect: match the project's last-saved compiler version.
Pass `-CodesysExe` / `-ProjectInfo` when auto-detect warns.
