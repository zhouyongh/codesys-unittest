# codesys-unittest - engineering guide

How to use this skill on a real project: write a feature with tests, run
regression, read the report, and what the agent prompt should look like.

## 1. Test layout (xunit vocabulary)

In a codesys-sync repo the test POUs live in the Application tree, next to the code:

```
<repo>/
  projects/<App>.project          # binary CODESYS project (not committed)
  src/plc/<Sys>/                  # production source (codesys-sync)
    Application/
      F_<Feature>.st              # feature under test
      GVL_Test.st                 # result protocol (copy from skill lib/)
      UT_Case.st
      FB_Assert.st + FB_Assert/   # assert helpers
      FB_<Feature>_Test.st + ...  # one suite per feature
      PRG_Tests.st                # suite registry (test builds only)
  projects/out/                   # report.txt + junit.xml + results.json (default, -OutDir to move)
```

`examples/sample-app/` keeps the same content as `tests/` + `Application/` staging:
copy its `Application/*` and `tests/*` into `src/plc/<Sys>/Application/`, or point
codesys-sync at it. `tests/` is only a staging folder - the `// PATH:` headers are
already `Application/...`.

Rules:

| Concept | In ST | Naming |
|---|---|---|
| Suite | FUNCTION_BLOCK | `FB_<Feature>_Test` |
| Test case | METHOD on the suite | `Test_<whatItDoes>` |
| Fixture | `VAR` on the suite | initialize in `VAR` / before `Begin` |
| Assert | `ass.AssertEquals_*` / `AssertTrue` | first arg = `Suite.Test_name` |
| Registry | `PRG_Tests` | call each suite; set `g_uiSuitesTotal` |

Keep tests **pure** when possible (no wall-clock, no hardware side effects) so
they pass on SoftMotion simulation **and** on a real PLC. Hardware-facing tests
go in a separate suite and are skipped with `ass.Skip(...)`.

### Reset protocol (why two runs in a row stay correct)

FB instance flags (`xStarted` / `xFinished`) survive a re-login. The host arms
each run and **verifies** the arm before polling:

1. pulse `GVL_Test.g_xReset := TRUE`
2. while reset is held: zero `g_xDone`, `g_uiCaseCount`, `g_uiFailCount`,
   `g_uiSkipCount`, `g_uiSuitesDone`, `g_xOverflow`
3. read back `g_xDone=0`, `g_uiCaseCount=0` and `g_uiFailCount=0`; abort the run if not
4. release `g_xReset := FALSE`
5. poll `g_xDone`

`FB_Assert.Begin` returns FALSE while `g_xReset` is TRUE and after a suite has
finished, so cases are recorded exactly once per run. The runner holds the reset
for 1 s, so the test task must run faster than that (1-100 ms is typical).
`ut.ps1 run` does all of this - you do not wire it yourself.

The run is only green with positive evidence: at least one case, all registered
suites finished (`g_uiSuitesDone == g_uiSuitesTotal`), no overflow, and the PLC
fail counter equal to the failed records that were read.

## 2. Writing a feature (red -> green)

1. Create `FB_<Feature>_Test` with the cases you already know you want:
   - happy path
   - boundary (min / max / zero)
   - one failure/guard case
2. Register it in `PRG_Tests` (`g_uiSuitesTotal` += 1).
3. Download (codesys-connect), then `ut.ps1 run` - **red is expected**.
4. Implement the feature until green.
5. Keep the suite. It is now regression.

Agent prompt shape (feature):

```
Implement <feature> in <path>.
Add FB_<Feature>_Test (xunit style) covering happy path, boundary, guard.
Register it in PRG_Tests and bump g_uiSuitesTotal.
Run: powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\ut.ps1 run `
     -Project <abs .project> -UserFile <user.txt>
Do not commit credentials. Use `ut.ps1 -Change Never|Keep` only; Force/Try are rejected by design.
```

## 3. Regression

Two steps, every time - the run itself never downloads:

```
# only when logic changed (import + full download, clears variables)
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-connect>\cc.ps1 connect -Project <proj> -UserFile user.txt
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-connect>\cc.ps1 download
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-connect>\cc.ps1 start

# always: run and gate
powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\ut.ps1 run `
    -Project <abs .project> -UserFile user.txt [-Address ip -Port n]
```

- Exit code 0 = green, 1 = red, zero cases, or pipeline error. Use it as the CI gate.
- `<OutDir>/report.txt` for humans, `<OutDir>/junit.xml` for CI (Jenkins/GitLab/GitHub).
- On a real PLC: pass `-Address`/`-Port`. The runner will not start/stop the
  remote runtime; it only checks the port and does not start a stopped app unless
  `-StartIfStopped` is given.

## 4. Report shape

`<OutDir>/report.txt` (default `projects/out/`):

```
CODESYS unit tests - 3 cases, 1 failed, 1 skipped
PASS  Sample.Test_add
FAIL  Sample.Test_divZeroGuard  expected TRUE
SKIP  Sample.Test_slow  not on this target
JUnit: .../out/junit.xml
```

`<OutDir>/junit.xml` - standard `<testsuite>/<testcase>/<failure>/<skipped>`; counters
match the emitted nodes. Pipeline errors (missing `GVL_Test`, login refused,
ineffective reset, timeout, zero cases) appear as a failing `pipeline` test case so
a red run is never silent.

`<OutDir>/results.json` (copied from the work dir) is the raw contract between the PLC
and the report:

```json
{
  "done": true,
  "caseCount": 3, "failCount": 1, "skipCount": 0,
  "durationSec": 1.2,
  "cases": [
    {"sName": "Sample.Test_add", "eStatus": 0, "sMessage": "", "sSuite": "Sample"}
  ]
}
```

## 5. Simulation vs real PLC

| | SoftMotion Win / Control Win | Real PLC |
|---|---|---|
| Runtime | `ensure-runtime` starts/restarts it (resolved install only) | you start it |
| Address | `127.0.0.1:11740` (default) | `-Address <ip> -Port <port>` |
| App state | started automatically | must be RUN, or pass `-StartIfStopped` |
| License | demo ~2h, auto-restart (`-MaxAgeHours`) | site policy |
| Tests | full suite | full suite; hardware cases may `Skip` |

DeviceID must match the runtime (SoftMotion Win x64 = `4102/0000 0004`) or
login fails - same rule as codesys-connect.

## 6. Safety rails (do not break these)

- Credentials: `-UserFile` or env. Never write passwords into the repo or work files.
- Login option: `change=Never` or `Keep`. **`Force` / `Try` are rejected** by the CLI
  (Force = full download, stops the app, clears variables). `run` never logs in
  with Try either - it would update the running program behind the user's back.
- Timeout cleanup kills only this run's process tree; never the user's IDE or a
  runtime from another install.
- UTF-8 everywhere. Do not rewrite sources as ASCII.
- This skill ships on GitHub: no machine paths, no usernames, no secrets.

## 7. What the agent should do every time

1. `ut.ps1 status` - is the runtime up? (exit 0 = port open)
2. If logic changed: codesys-connect `download`, then `start`.
3. `ut.ps1 run -Project ... -UserFile ...`
4. Read the report (`<OutDir>/report.txt`). If red, fix code or test, rerun.
5. Never commit `user.txt`, session files, or the report directory unless the repo wants reports.
