// FB_Sample_Test - minimal xunit-style suite (template, method-free body).
// Prefer FB_F_Clamp_Test + methods for real suites; this one shows the
// smallest possible suite shape.
// PATH: <Application>/FB_Sample_Test
FUNCTION_BLOCK FB_Sample_Test
VAR
    ass : FB_Assert;
    lrA : LREAL;
    lrB : LREAL;
END_VAR
// ===== IMPLEMENTATION =====
IF NOT ass.Begin('Sample') THEN
    RETURN;
END_IF
lrA := 10.0;
lrB := 3.0;
ass.AssertEquals_LREAL('Sample.Test_add', 13.0, lrA + lrB, 0.0001);
ass.AssertEquals_LREAL('Sample.Test_sub', 7.0, lrA - lrB, 0.0001);
ass.AssertFalse('Sample.Test_divZeroGuard', lrB = 0.0);
ass.Finish();
