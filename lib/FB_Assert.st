// PATH: <Application>/FB_Assert
// ===== DECLARATION =====
FUNCTION_BLOCK FB_Assert
VAR
    xStarted : BOOL;
    xFinished : BOOL;
    sSuite : STRING(40);
END_VAR
// ===== IMPLEMENTATION =====
IF GVL_Test.g_xReset THEN
    xStarted := FALSE;
    xFinished := FALSE;
    RETURN;
END_IF