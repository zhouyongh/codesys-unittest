// PATH: Application/PRG_Tests
// ===== DECLARATION =====
PROGRAM PRG_Tests
VAR
    fbClamp : FB_F_Clamp_Test;
END_VAR
// ===== IMPLEMENTATION =====
// Must match the number of suites called below. The runner cross-checks
// g_uiSuitesDone against this value, so a stale count fails the run.
GVL_Test.g_uiSuitesTotal := 1;
fbClamp();
