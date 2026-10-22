# conveyor-loop - closed-loop sample (basic conveyor sort)

A mid-sized sample for the **feature → red → green → regression** loop with
codesys-unittest. Domain: a belt, a quality sensor, a pneumatic diverter,
and piece counters. No motion axes, so the same code runs on SoftMotion
simulation and on a real PLC.

## Features

| # | Object | What it does | Suite |
|---|---|---|---|
| 1 | `F_DecideSort` | push to reject lane when quality is NG | `FB_DecideSort_Test` (3 methods / 3 cases) |
| 2 | `FB_Diverter` | delay → extend → retract, `Step(dtMs)` testable | `FB_Diverter_Test` (3 methods / 7 cases) |
| 3 | `FB_Conveyor` | run / stop / e-stop interlock + latch | `FB_Conveyor_Test` (5 methods / 5 cases) |
| 4 | `FB_Stats` | pass / reject / total counters (edge) | `FB_Stats_Test` (2 methods / 4 cases) |

**13 test methods, 19 cases, 4 suites.** In this runner one `ass.Assert*` call is
one case, so a method with four assertions contributes four cases. Test objects
live under `Application/Tests` in the project; the protocol copies there match
`lib/` except for the `// PATH` prefix.

## Put it into a codesys-sync repo

The sample ships as a source tree, not as a repo with a `.project`. Copy it in:

```text
<repo>/
  projects/<App>.project
  src/plc/<App>/Application/          <- copy examples/conveyor-loop/Application/* here
  src/plc/<App>/Application/Tests/    <- copy examples/conveyor-loop/Tests/* here
  src/plc/<App>/structure_ops.txt     <- copy examples/conveyor-loop/structure_ops.txt here
```

`structure_ops.txt` creates the `Tests` folder, the protocol, the suites and
`PRG_Tests`, then assigns `PRG_Tests` to `MainTask`. If your Application node or
task has another name, adjust the paths.

## Closed loop (same command every round)

```powershell
# 1) write / change ST under Application/ or Application/Tests/
# 2) import into the .project (structure_ops creates the objects)
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-sync>\import.ps1 `
    -Root <repo> -Select 1 -Yes -Sync -VerifyBuild

# 3) download only when logic changed
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-connect>\cc.ps1 download

# 4) run the tests
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-unittest>\ut.ps1 run `
    -Project <abs .project> -UserFile <user.txt>
```

Read `<OutDir>/report.txt` and `junit.xml`. Exit code is the gate.

## Suggested walk-through

1. **Feature 1 red** – stub `F_DecideSort` to `FALSE`, import + download + run →
   1 of 3 fails (`DecideSort.Test_QualityNgPushes`).
2. **Feature 1 green** – implement the rule → 3 cases pass.
3. **Feature 2–4** – same red→green rhythm; add the suite to `PRG_Tests` and
   keep `g_uiSuitesTotal` equal to the number of suites actually called (it is
   computed from `g_sFilter`).
4. **Regression** – remove only the e-stop branch from `FB_Conveyor`, then
   import + download + run → 1 of 19 fails (`Conveyor.Test_EStopWins`).
   Import + download is required: `ut.ps1 run` never downloads.
5. **Restore** – put the branch back, import + download + run → 19 pass.
6. **Two runs in a row** – run again without downloading → still 19 pass.
   The counter suites assert deltas, not absolute values.

Full narrative and expected output: [docs/CLOSED_LOOP.md](docs/CLOSED_LOOP.md).
Suite style (headers, Setup/TearDown, naming): [docs/TEST_STYLE.md](docs/TEST_STYLE.md).

## Layout

```text
Application/                 # production features
  F_DecideSort.st
  FB_Diverter.st
  FB_Conveyor.st
  FB_Stats.st
Tests/                      # test POUs (imported as Application/Tests)
  UT_Case.st GVL_Test.st FB_Assert.st + methods
  FB_<Unit>_Test.st + methods (Setup / TearDown / Test_*)
  PRG_Tests.st
structure_ops.txt
docs/CLOSED_LOOP.md
docs/TEST_STYLE.md
```
