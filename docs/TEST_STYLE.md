# Test style rules (PLC suites)

Rules for suites written with codesys-unittest. The sample
`examples/conveyor-loop/` is the reference implementation.

## 1. Folder

All test objects live in an organizational folder **`Tests`** under the
Application. Production features stay outside it.

```text
Application/
  FB_Diverter.st              # feature (under test)
  Tests/
    FB_Assert.st + methods    # test protocol
    GVL_Test.st / UT_Case.st  # result protocol
    FB_Diverter_Test.st       # suite
    FB_Diverter_Test/
      Test_....st
    PRG_Tests.st              # registry (optional here or at Application)
```

## 2. Naming

| Object | Name | Example |
|---|---|---|
| Suite FUNCTION_BLOCK | `FB_<Unit>_Test` | unit `FB_Diverter` → `FB_Diverter_Test` |
| Test METHOD | `Test_<behaviour>` | `Test_ExtendsAfterDelay` |
| Fixture instance | short type name | `fb : FB_Diverter` |

Drop an extra letter (`FB_F_Diverter_Test` is wrong). The suite name is the
unit name plus `_Test`, implemented as a FUNCTION_BLOCK.

## 3. Suite header (required)

Every `FB_<Unit>_Test` declaration starts with this block (before
`FUNCTION_BLOCK`):

```st
// ===== TEST SUITE =====
// unit   : FB_Diverter
// purpose: one-shot diverter (delay / extend / retract) and push count
// cases  : Test_DoesNotPushWhenIdle
//          Test_ExtendsAfterDelayThenRetracts
//          Test_CountsCompletedPushes
// fixture: local fb : FB_Diverter per case (no shared state)
// tags   : unit, pure
// ===== DECLARATION =====
```

- **unit** – object under test (path-friendly name).
- **purpose** – one or two lines, what this suite protects.
- **cases** – full list of `Test_*` names, one per line (must match methods).
- **fixture** – how state is prepared (`Setup` / local instance / constants).
- **tags** – free-form (`unit`, `timing`, `remote`, …).

## 4. Test method header (required)

Every `Test_*` method starts with:

```st
// ===== TEST CASE =====
// name : Test_ExtendsAfterDelayThenRetracts
// intent: cylinder must stay in during delay, go out, then retract
// steps : 1) fire xTrigger for one scan
//         2) Step(10) twelve times
// expects: saw xCylinder TRUE at least once, xDone TRUE, cylinder out FALSE
// ===== DECLARATION =====
```

- **name** – same as the method name.
- **intent** – the behaviour being proved (not the code).
- **steps** – short arrange/act list.
- **expects** – what must be true for PASS.

## 5. TestResult summary

`GVL_Test` is the single online summary (watch this GVL in the IDE):

| Field | Meaning |
|---|---|
| `g_uiSuitesTotal` / `g_uiSuitesDone` | how many suites, how many finished |
| `g_uiCaseCount` / `g_uiFailCount` / `g_uiSkipCount` | planned cases run, failed, skipped |
| `g_sFilter` | empty = all suites; a name = run/report only that suite |
| `g_sFirstFailure` | first failure message (empty if green) |
| `g_astCases[i].sName` | case id (`Suite.Test_xxx`) |
| `g_astCases[i].eStatus` | 0=pass 1=fail 2=skip |
| `g_astCases[i].sMessage` | why it failed / was skipped |

One case = one assertion result. A suite may call several asserts in one
method; each `Rec` is one row. To run a single suite, set `g_sFilter` to the
suite name (`FB_Diverter_Test` or `Diverter`) before the run. It is empty by
default; the host runner does not change it, and `PRG_Tests` computes
`g_uiSuitesTotal` from the selected suites.

## 6. Setup / Teardown

xunit-style fixture hooks on the suite:

- `METHOD PUBLIC Setup` – per case, before the body.
- `METHOD PUBLIC TearDown` – per case, after the body.

The suite body wraps every case:

```st
Setup();
Test_DoesNotPushWhenIdle();
TearDown();
Setup();
Test_ExtendsAfterDelayThenRetracts();
TearDown();
```

Rules:

- `Setup` prepares `fb` / inputs; `TearDown` clears outputs and one-shot flags.
- Do not leave shared instances dirty across cases (each case must pass alone).
- `ass.Begin` / `ass.Finish` stay outside the per-case hooks (suite lifetime).

## 7. Checklist before you commit a suite

- [ ] Lives under `Tests/`
- [ ] Name is `FB_<Unit>_Test`
- [ ] Suite header lists every `Test_*`
- [ ] Each `Test_*` has a case header
- [ ] `Setup` / `TearDown` wrap each case
- [ ] `PRG_Tests.g_uiSuitesTotal` matches the selected suites (all or the
      `g_sFilter` subset)
- [ ] `ut.ps1 run` green; break one expect and see it go red
