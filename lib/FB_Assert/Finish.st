// PATH: Application/FB_Assert/Finish
// ===== DECLARATION =====
METHOD PUBLIC Finish
// ===== IMPLEMENTATION =====
IF xFinished THEN
    RETURN;
END_IF
xFinished := TRUE;
GVL_Test.g_uiSuitesDone := GVL_Test.g_uiSuitesDone + 1;
IF GVL_Test.g_uiSuitesTotal > 0 AND GVL_Test.g_uiSuitesDone >= GVL_Test.g_uiSuitesTotal THEN
    GVL_Test.g_xDone := TRUE;
    GVL_Test.g_xRunning := FALSE;
END_IF
