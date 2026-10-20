// PATH: <Application>/FB_Assert/Rec
// ===== DECLARATION =====
METHOD PRIVATE Rec : BOOL
VAR_INPUT
    sName : STRING(80);
    xOk : BOOL;
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
    Rec := FALSE; RETURN;
END_IF
uiIdx := GVL_Test.g_uiCaseCount + 1;
GVL_Test.g_uiCaseCount := uiIdx;
GVL_Test.g_astCases[uiIdx].sName := sName;
IF xOk THEN
    GVL_Test.g_astCases[uiIdx].eStatus := UT_PASS;
    GVL_Test.g_astCases[uiIdx].sMessage := '';
ELSE
    GVL_Test.g_astCases[uiIdx].eStatus := UT_FAIL;
    GVL_Test.g_astCases[uiIdx].sMessage := sMessage;
    GVL_Test.g_uiFailCount := GVL_Test.g_uiFailCount + 1;
END_IF
Rec := xOk;
