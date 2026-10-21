# sample-app - minimal feature + test (codesys-unittest)

Demonstrates the feature workflow from `docs/ENGINEERING.md`. Every `.st` file here
carries the codesys-sync header and a concrete `// PATH: Application/...`, so the
tree can be imported without editing.

| File | Role |
|---|---|
| `Application/F_Clamp.st` | feature under test (pure function) |
| `tests/UT_Case.st` | case record DUT (required by GVL_Test) |
| `tests/GVL_Test.st` | result protocol GVL |
| `tests/FB_Assert.st` + `tests/FB_Assert/` | assert helpers (methods) |
| `tests/FB_F_Clamp_Test.st` + `tests/FB_F_Clamp_Test/` | xunit-style suite (5 cases) |
| `tests/FB_Sample_Test.st` | optional minimal suite shape - **not** registered in PRG_Tests |
| `tests/PRG_Tests.st` | registry (`g_uiSuitesTotal := 1`) |
| `structure_ops.txt` | codesys-sync structure operations for a one-shot import |

`tests/` is a staging folder: its contents belong in the Application node, which is
why their `PATH` is `Application/...` (the `tests/` segment is not part of the path).

## Wire it into a CODESYS project

1. Create/open a SoftMotion Win **x64** project (DeviceID `4102/0000 0004`).
2. Put the sources where codesys-sync expects them:
   `<repo>/src/plc/<Sys>/Application/F_Clamp.st`, `.../Application/GVL_Test.st`, etc.
   (merge `Application/` and `tests/` into that one folder), then copy
   `structure_ops.txt` to `<repo>/src/plc/<Sys>/structure_ops.txt`.
3. Import and build:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-sync>\import.ps1 -Root <repo> -Sync -VerifyBuild
   ```
   `-Sync` also creates methods missing from the project; without it, the
   `CREATE_METHOD` lines in `structure_ops.txt` create the shells first.
   If your Application node is not named `Application`, replace the first segment
   of every `// PATH:` (and of `structure_ops.txt`) accordingly.
4. Make sure `PRG_Tests` is assigned to a cyclic task. `ASSIGN_TO_TASK` assumes
   `Application/Task Configuration/MainTask`; adjust it if your task is named
   differently. Leave `PRG_Main` out of a pure test application.
5. Download + start, then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File <codesys-unittest>\ut.ps1 run `
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

Break `F_Clamp` on purpose (e.g. swap the return for `lrValue` always), download,
and rerun - the report turns red and `junit.xml` marks the failing case. Restore,
download, rerun: green again.
