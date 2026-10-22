// PATH: Application/Tests/FB_Assert/AssertEquals_LREAL
// ===== DECLARATION =====
METHOD PUBLIC AssertEquals_LREAL : BOOL
VAR_INPUT
    sName : STRING(80);
    lrExpected : LREAL;
    lrActual : LREAL;
    lrEps : LREAL;
END_VAR
VAR
    lrDiff : LREAL;
END_VAR
// ===== IMPLEMENTATION =====
lrDiff := lrExpected - lrActual;
IF lrDiff < 0.0 THEN
    lrDiff := -lrDiff;
END_IF
AssertEquals_LREAL := Rec(sName, lrDiff <= lrEps, 'lreal mismatch');
