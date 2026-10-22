// PATH: Application/Tests/FB_Assert/AssertEquals_DINT
// ===== DECLARATION =====
METHOD PUBLIC AssertEquals_DINT : BOOL
VAR_INPUT
    sName : STRING(80);
    diExpected : DINT;
    diActual : DINT;
END_VAR
// ===== IMPLEMENTATION =====
AssertEquals_DINT := Rec(sName, diExpected = diActual, 'dint mismatch');
