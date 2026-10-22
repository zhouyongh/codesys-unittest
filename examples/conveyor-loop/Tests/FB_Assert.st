// PATH: Application/Tests/FB_Assert
// ===== DECLARATION =====
FUNCTION_BLOCK FB_Assert
VAR
    xStarted : BOOL;
    xFinished : BOOL;
    sSuite : STRING(40);
END_VAR
// ===== IMPLEMENTATION =====
// No body logic on purpose: calling a method does not execute the FB body.
// One-shot state is handled by Begin / Finish / ResetState, and Begin clears
// it while GVL_Test.g_xReset is TRUE.
