# Closed-loop walk-through - conveyor sort

This page is the narrative behind `examples/conveyor-loop/`. It shows how a
feature grows with tests: red first, then green, then a deliberate regression.

## Setup

1. A CODESYS project with a cyclic task (SoftMotion Win x64 works).
2. codesys-sync `import.ps1` can write `Application/` objects.
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

Expected report (red):

```text
CODESYS unit tests - 3 cases, 1 failed, 0 skipped
PASS  DecideSort.Test_NoPieceNeverPushes
PASS  DecideSort.Test_QualityOkPasses
FAIL  DecideSort.Test_QualityNgPushes  expected TRUE
```

**Close the gap.** Implement the rule: no piece → no push; quality OK →
pass; quality NG → push. Run again (green):

```text
CODESYS unit tests - 3 cases, 0 failed, 0 skipped
PASS  DecideSort.Test_NoPieceNeverPushes
PASS  DecideSort.Test_QualityOkPasses
PASS  DecideSort.Test_QualityNgPushes
```

Exit code is now 0. Keep the suite.

## Round 2 - the diverter

Add `FB_Diverter` with `Step(dtMs)` so multi-cycle behaviour is testable in
one call. Ship it as "cylinder out always" first →
`Diverter.Test_ExtendsAfterDelayThenRetracts` fails. Then implement the
phase sequence (delay / extend / retract) → 3 cases pass.

`dtMs` is an input on purpose: tests drive 10 ms steps inside a single
`Test_*` method and assert cylinder / busy / done, without wall-clock.

## Round 3 - belt and counters

`FB_Conveyor` (e-stop wins) and `FB_Stats` (edge counters) follow the same
rhythm. Remember to bump `g_uiSuitesTotal` in `PRG_Tests` when a suite is
added, otherwise the runner reports `g_xDone fired after N of M suites`.

## Round 4 - regression is a command

With all 11 cases green, break one rule on purpose, e.g. in `FB_Conveyor`:

```st
// ELSIF ... wrong on purpose
IF xStart THEN xRun := TRUE; END_IF   // ignores e-stop
```

Run the **same** `ut.ps1 run` (no other step):

```text
CODESYS unit tests - 11 cases, 1 failed, 0 skipped
...
FAIL  Conveyor.Test_EStopWins  expected FALSE
```

`junit.xml` carries the same failure for CI. Restore the interlock, run
again → full green, exit 0. That is the loop.

## What "closed" means

| Step | Tool | Artefact |
|---|---|---|
| write feature + suite | editor | `.st` sources |
| import | codesys-sync | `.project` |
| download (logic changed) | codesys-connect | running app |
| run | codesys-unittest | `report.txt` / `junit.xml` / exit code |

Nothing in that table is special to this sample; the conveyor domain is
just an easy story to tell while the loop itself stays generic.
