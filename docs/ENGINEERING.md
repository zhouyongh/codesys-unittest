# codesys-unittest - engineering guide

How to use this skill on a real project: write a feature with tests, run
regression, read the report, and what the agent prompt should look like.

## 1. Test layout (xunit vocabulary)

```
<repo>/
  projects/<App>.project          # binary CODESYS project
  src/...                         # production source (codesys-sync)
  tests/                          # test POUs (committed)
    GVL_Test.st                   # result protocol (copy from skill lib/)
    FB_Assert.st                  # assert helpers
    FB_<Feature>_Test.st          # one suite per feature
    PRG_Tests.st                  # suite registry (test application only)
```

Rules:

| Concept | In ST | Naming |
|---|---|---|
| Suite | FUNCTION_BLOCK | `FB_<Feature>_Test` |
| Test case | METHOD on the suite | `Test_<whatItDoes>` |
| Fixture | `VAR` + `Setup()` | reset inputs before each case |
| Assert | `ass.AssertEquals_*` / `AssertTrue` | first arg = `Suite.Test_name` |
| Registry | `PRG_Tests` | call each suite; set `g_uiSuitesTotal` |

Keep tests **pure** when possible (no wall-clock, no hardware side effects) so
they pass on SoftMotion simulation **and** on a real PLC. Hardware-facing tests
go in a separate suite and are skipped with `ass.Skip(...)` when the target
cannot support them.

### Reset protocol (why two runs in a row stay correct)

CODESYS FB instance flags (`xStarted` / `xFinished`) survive a re-login. The
host therefore **arms** each run before polling:

1. pulse `GVL_Test.g_xReset := TRUE` (suites clear their one-shot flags)
2. zero `g_xDone`, `g_uiCaseCount`, `g_uiFailCount`, `g_uiSkipCount`, `g_uiSuitesDone`
3. pulse `g_xReset := FALSE`
4. poll `g_xDone`

`FB_Assert.Begin` returns FALSE while `g_xReset` is TRUE and after a suite has
finished, so cases are recorded exactly once per run. `ut.ps1 run` does this
automatically - you do not wire it yourself.

## 2. Writing a feature (red -> green)

1. Create `FB_<Feature>_Test` with the cases you already know you want:
   - happy path
   - boundary (min / max / zero)
   - one failure/guard case
2. Register it in `PRG_Tests` (`g_uiSuitesTotal` += 1).
3. Run `ut.ps1 run` - **red is expected**. The report tells you which assert fired.
4. Implement the feature until green.
5. Keep the suite. It is now regression.

Agent prompt shape (feature):

```
Implement <feature> in <path>.
Add FB_<Feature>_Test (xunit style) covering happy path, boundary, guard.
Register it in PRG_Tests.
Run: powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\ut.ps1 run `
     -Project <abs .project> -UserFile <user.txt>
Do not commit credentials. Do not use OnlineChangeOption.Force.
```

## 3. Regression

Same command every time - no special mode:

```
powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\ut.ps1 run `
    -Project <abs .project> -UserFile <user.txt> [-Address ip -Port n]
```

- Exit code 0 = green, 1 = red or pipeline error. Use it as the CI gate.
- `out/report.txt` for humans, `out/junit.xml` for CI (Jenkins/GitLab/GitHub).
- On a real PLC: pass `-Address`/`-Port`. The runner will not start/stop the
  remote runtime - only check the port.
- Full suite download uses codesys-connect `download` first when logic changed.
  `ut.ps1 run` itself logs in with `change=Never` and will **not** download.

## 4. Report shape

`out/report.txt`:

```
CODESYS unit tests - 3 cases, 1 failed, 0 skipped
PASS  Sample.Test_add
FAIL  Sample.Test_divZeroGuard  expected TRUE
PASS  Sample.Test_divZeroGuard_result
JUnit: .../out/junit.xml
```

`out/junit.xml` - standard `<testsuite>/<testcase>/<failure>`; CI dashboards
render it natively. Pipeline errors (missing `GVL_Test`, login refused, timeout)
appear as a failing `pipeline` testcase so a red run is never silent.

`results.json` (work dir) is the raw contract between the PLC and the report:

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
| Runtime | `ensure-runtime` starts/restarts it | you start it |
| Address | `127.0.0.1:11740` (default) | `-Address <ip> -Port <port>` |
| License | demo ~2h, auto-restart | site policy |
| Tests | full suite | full suite; hardware cases may `Skip` |

DeviceID must match the runtime (SoftMotion Win x64 = `4102/0000 0004`) or
login fails - same rule as codesys-connect.

## 6. Safety rails (do not break these)

- Credentials: `-UserFile` or env. Never write passwords into the repo or work files.
- Login option: `change=Never` by default. **Never** auto-escalate to `Force`
  (Force = full download, stops the app, clears variables).
- UTF-8 everywhere. Do not rewrite sources as ASCII.
- This skill ships on GitHub: no machine paths, no usernames, no secrets.

## 7. What the agent should do every time

1. `ut.ps1 status` - is the runtime up?
2. If logic changed: codesys-connect `download` (explicit), then `start`.
3. `ut.ps1 run -Project ... -UserFile ...`
4. Read `out/report.txt`. If red, fix code or test, rerun.
5. Never commit `user.txt`, session files, or `out/` unless the repo wants reports.
