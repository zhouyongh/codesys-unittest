// PATH: Application/FB_Assert/Begin
// ===== DECLARATION =====
METHOD PUBLIC Begin : BOOL
VAR_INPUT
    sName : STRING(40);
END_VAR
// ===== IMPLEMENTATION =====
IF GVL_Test.g_xReset THEN
    xStarted := FALSE;
    xFinished := FALSE;
    Begin := FALSE; RETURN;
END_IF
IF xStarted OR xFinished THEN
    Begin := FALSE; RETURN;
END_IF
xStarted := TRUE;
xFinished := FALSE;
sSuite := sName;
GVL_Test.g_xRunning := TRUE;
Begin := TRUE;
