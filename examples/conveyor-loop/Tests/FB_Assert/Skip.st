// PATH: Application/Tests/FB_Assert/Skip
// ===== DECLARATION =====
METHOD PUBLIC Skip
VAR_INPUT
    sName : STRING(80);
    sMessage : STRING(120);
END_VAR
VAR
    uiIdx : UINT;
END_VAR
// ===== IMPLEMENTATION =====
IF NOT xStarted THEN
    Begin('Unnamed');
END_IF
IF GVL_Test.g_uiCaseCount >= UT_MAX_CASES THEN
    GVL_Test.g_xOverflow := TRUE;
    RETURN;
END_IF
uiIdx := GVL_Test.g_uiCaseCount + 1;
GVL_Test.g_uiCaseCount := uiIdx;
GVL_Test.g_uiSkipCount := GVL_Test.g_uiSkipCount + 1;
GVL_Test.g_astCases[uiIdx].sName := sName;
GVL_Test.g_astCases[uiIdx].eStatus := UT_SKIP;
GVL_Test.g_astCases[uiIdx].sMessage := sMessage;
