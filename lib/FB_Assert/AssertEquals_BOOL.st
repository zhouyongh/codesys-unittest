// PATH: <Application>/FB_Assert/AssertEquals_BOOL
// ===== DECLARATION =====
METHOD PUBLIC AssertEquals_BOOL : BOOL
VAR_INPUT
    sName : STRING(80);
    xExpected : BOOL;
    xActual : BOOL;
END_VAR
// ===== IMPLEMENTATION =====
AssertEquals_BOOL := Rec(sName, xExpected = xActual, 'bool mismatch');
