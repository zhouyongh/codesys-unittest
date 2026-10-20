// PATH: <Application>/GVL_Test
// ===== DECLARATION =====
VAR_GLOBAL CONSTANT
    UT_MAX_CASES : UINT := 64;
    UT_PASS : UINT := 0;
    UT_FAIL : UINT := 1;
    UT_SKIP : UINT := 2;
END_VAR

VAR_GLOBAL
    g_xRunning : BOOL;
    g_xDone : BOOL;
    g_xReset : BOOL;
    g_uiCaseCount : UINT;
    g_uiFailCount : UINT;
    g_uiSkipCount : UINT;
    g_uiSuitesTotal : UINT;
    g_uiSuitesDone : UINT;
    g_astCases : ARRAY[1..64] OF UT_Case;
END_VAR
// ===== IMPLEMENTATION =====