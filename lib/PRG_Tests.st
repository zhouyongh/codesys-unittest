// PATH: <Application>/PRG_Tests
// ===== DECLARATION =====
PROGRAM PRG_Tests
VAR
    fbClamp : FB_F_Clamp_Test;
    xAllFinished : BOOL;
END_VAR
// ===== IMPLEMENTATION =====
GVL_Test.g_uiSuitesTotal := 1;
fbClamp();
xAllFinished := GVL_Test.g_xDone;