# Closed-loop walk-through - conveyor sort

This page is the narrative behind `examples/conveyor-loop/`. It shows how a
feature grows with tests: red first, then green, then a deliberate regression,
then two runs in a row without downloading.

In this runner **one `ass.Assert*` call is one case**. The sample has 13 test
methods and 19 cases; a method with four assertions contributes four cases.

## Setup

1. Copy the sample into a codesys-sync repo (see the README):
   `src/plc/<App>/Application/` + `src/plc/<App>/structure_ops.txt`.
2. A CODESYS project with a cyclic task `MainTask` (SoftMotion Win x64 works).
3. codesys-connect credentials in a local `user.txt` (not committed).
4. SoftMotion / Control Win running (`ut.ps1 ensure-runtime`).

## Round 1 - decide what to sort

**Source.** Add `F_DecideSort` and `FB_F_DecideSort_Test`. Keep the
implementation a stub so the suite is honest about the gap:

```st
F_DecideSort := FALSE;   // stub
```

Import, download, run:

```powershell
ut.ps1 run -Project <abs .project> -UserFile <user.txt>
```

Expected report (red, 1 of 3):

```text
CODESYS unit tests - 3 cases, 1 failed, 0 skipped
PASS  DecideSort.Test_NoPieceNeverPushes
PASS  DecideSort.Test_QualityOkPasses
FAIL  DecideSort.Test_QualityNgPushes  expected TRUE
```

**Close the gap.** Implement the rule: no piece → no push; quality OK →
pass; quality NG → push. Import + download + run (green):

```text
CODESYS unit tests - 3 cases, 0 failed, 0 skipped
PASS  DecideSort.Test_NoPieceNeverPushes
PASS  DecideSort.Test_QualityOkPasses
PASS  DecideSort.Test_QualityNgPushes
```

Exit code is now 0. Keep the suite.

## Round 2 - the diverter

Add `FB_Diverter` with `Step(dtMs)` so multi-cycle behaviour is testable in one
call. The suite has 3 methods and 7 cases.

Ship it as "cylinder out always" first → 3 of 7 fail: the delay case
(`Diverter.Test_not_extended_before_delay`), the retracted case
(`Diverter.Test_cylinder_retracted`) and the idle case
(`Diverter.Test_DoesNotPushWhenIdle`). Then implement the phase sequence
(delay / extend / retract) → 7 cases pass.

`dtMs` is an input on purpose: tests drive 10 ms steps inside a single
`Test_*` method and assert cylinder / busy / done, without wall-clock.

## Round 3 - belt and counters

`FB_Conveyor` (5 methods / 5 cases) and `FB_Stats` (2 methods / 4 cases) follow
the same rhythm. The counter assertions use **deltas**, not absolute values, so
a second run without downloading stays green.

`PRG_Tests` must set `g_uiSuitesTotal := 4` and call all four suites.

## Round 4 - regression needs import + download

With all 19 cases green, break one rule on purpose. Remove **only** the e-stop
branch from `FB_Conveyor`:

```st
// before
IF NOT xEStop THEN
    xRun := FALSE;
ELSIF xStop THEN
    xRun := FALSE;
ELSIF xStart THEN
    xRun := TRUE;
END_IF

// broken: e-stop branch removed, stop branch kept
IF xStop THEN
    xRun := FALSE;
ELSIF xStart THEN
    xRun := TRUE;
END_IF
```

Then apply it and run the **same** test command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-sync>\import.ps1 `
    -Root <repo> -Select 1 -Yes -Sync -VerifyBuild
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-connect>\cc.ps1 download
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-unittest>\ut.ps1 run `
    -Project <abs .project> -UserFile <user.txt>
```

Expected report (19 cases, 1 failed):

```text
CODESYS unit tests - 19 cases, 1 failed, 0 skipped
...
FAIL  Conveyor.Test_EStopWins  expected FALSE
...
```

`junit.xml` carries the same failure for CI.

**Why import + download is in this round:** `ut.ps1 run` logs in with
`change=Never` and never downloads. A changed `.st` file on disk does not change
the running application; without import + download the run still tests the old
build.

## Round 5 - two runs in a row

Restore the e-stop branch, import + download + run → 19 pass. Now run the
**same command again without downloading**:

```powershell
ut.ps1 run -Project <abs .project> -UserFile <user.txt>
```

It must still be 19/19 green. This is the multi-round check:

- counter suites compare `uiPass` / `uiReject` / `uiTotal` / `uiPushCount`
  against a baseline captured in the same run;
- `Test_ExtendsAfterDelayThenRetracts` clears its own observation flags at the
  start;
- `FB_Assert.Begin` clears the suite one-shot flags while `g_xReset` is held.

## Round 6 (optional) - the runner's own guard

The sample is also a place to see the runner fail for a structural reason, not
just an assertion. Set the suite total wrong:

```st
GVL_Test.g_uiSuitesTotal := 5;   // four suites actually run
```

Import + download + run. The four suites finish, `g_xDone` is never set, and
after the poll timeout the runner reports:

```text
ERR timeout waiting for GVL_Test.g_xDone (60s) (suitesDone=4/5) ...
```

Exit code 1. Restore the value to 4. This is the difference between "a test
failed" and "the test run itself is not trustworthy".

## What "closed" means

| Step | Tool | Artefact |
|---|---|---|
| write feature + suite | editor | `.st` sources |
| import | codesys-sync | `.project` |
| download (logic changed) | codesys-connect | running app |
| run | codesys-unittest | `report.txt` / `junit.xml` / exit code |

Nothing in that table is special to this sample; the conveyor domain is
just an easy story to tell while the loop itself stays generic.
