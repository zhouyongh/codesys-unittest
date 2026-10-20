# sample-app - minimal feature + test (codesys-unittest)

Demonstrates the feature workflow from `docs/ENGINEERING.md`:

| File | Role |
|---|---|
| `Application/F_Clamp.st` | feature under test (pure function) |
| `tests/UT_Case.st` | case record DUT (required by GVL_Test) |
| `tests/GVL_Test.st` | result protocol GVL |
| `tests/FB_Assert.st` + `tests/FB_Assert/` | assert helpers (methods) |
| `tests/FB_F_Clamp_Test.st` + `tests/FB_F_Clamp_Test/` | xunit-style suite (5 cases) |
| `tests/PRG_Tests.st` | registry (`g_uiSuitesTotal := 1`) |
| `tests/FB_Sample_Test.st` | optional minimal suite shape - **not** registered in PRG_Tests |

## Wire it into a CODESYS project

1. Create/open a SoftMotion Win **x64** project (DeviceID `4102/0000 0004`).
2. Import the POUs above into the **test** application (or use codesys-sync import).
3. Assign `PRG_Tests` to a cyclic task. Leave `PRG_Main` out of the test app
   if you want a pure unit-test application.
4. Build, then:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\ut.ps1 run `
    -Project <abs .project> -UserFile <path to user.txt>
```

Expected green report:

```
CODESYS unit tests - 5 cases, 0 failed, 0 skipped
PASS  F_Clamp.Test_InsideRangeReturnsValue
PASS  F_Clamp.Test_BelowLowReturnsLow
PASS  F_Clamp.Test_AboveHighReturnsHigh
PASS  F_Clamp.Test_EqualBoundsReturnsBound
PASS  F_Clamp.Test_LowGreaterThanHighSwapsBounds
```

Break `F_Clamp` on purpose (e.g. swap the return for `lrValue` always) and rerun -
the report turns red and `junit.xml` marks the failing case.
