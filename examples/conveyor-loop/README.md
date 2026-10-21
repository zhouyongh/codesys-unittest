# conveyor-loop - closed-loop sample (basic conveyor sort)

A mid-sized sample for the **feature → red → green → regression** loop with
codesys-unittest. Domain: a belt, a quality sensor, a pneumatic diverter,
and piece counters. No motion axes, so the same code runs on SoftMotion
simulation and on a real PLC.

## Features

| # | Object | What it does | Suite |
|---|---|---|---|
| 1 | `F_DecideSort` | push to reject lane when quality is NG | `FB_F_DecideSort_Test` (3 cases) |
| 2 | `FB_Diverter` | delay → extend → retract, `Step(dtMs)` testable | `FB_F_Diverter_Test` (3 cases) |
| 3 | `FB_Conveyor` | run / stop / e-stop interlock | `FB_F_Conveyor_Test` (3 cases) |
| 4 | `FB_Stats` | pass / reject / total counters (edge) | `FB_F_Stats_Test` (2 cases) |

11 cases, 4 suites. Protocol POUs (`UT_Case`, `GVL_Test`, `FB_Assert`) come
from the skill `lib/`.

## Closed loop (same command every round)

```powershell
# 1) write / change ST under Application/
# 2) import into the .project
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-sync>\import.ps1 `
    -Root <repo> -Select 1 -Yes

# 3) download only when logic changed
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-connect>\cc.ps1 download

# 4) run the tests
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-unittest>\ut.ps1 run `
    -Project <abs .project> -UserFile <user.txt>
```

Read `<OutDir>/report.txt` and `junit.xml`. Exit code is the gate.

## Suggested walk-through

1. **Feature 1 red** – add `F_DecideSort` returning `FALSE` always, run → `DecideSort.Test_QualityNgPushes` fails.
2. **Feature 1 green** – implement the real rule, run → 3 cases pass.
3. **Feature 2–4** – same red→green rhythm; register each suite in `PRG_Tests`
   (`g_uiSuitesTotal` must match the number of suites).
4. **Regression** – break one rule (e.g. `FB_Conveyor` ignores e-stop), run →
   only `Conveyor.Test_EStopWins` fails, junit marks it.
5. **Restore** – run again → full green, exit 0.

Full narrative and expected output: [docs/CLOSED_LOOP.md](docs/CLOSED_LOOP.md).

## Layout

```text
Application/
  F_DecideSort.st          # feature (pure)
  FB_Diverter.st           # feature (stepped FB)
  FB_Conveyor.st           # feature (interlock)
  FB_Stats.st              # feature (counters)
  UT_Case.st GVL_Test.st FB_Assert.st + methods   # protocol
  FB_F_*_Test.st + methods                        # suites
  PRG_Tests.st
structure_ops.txt
```
