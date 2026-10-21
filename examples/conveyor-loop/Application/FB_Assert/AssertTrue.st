// PATH: Application/FB_Assert/AssertTrue
// ===== DECLARATION =====
METHOD PUBLIC AssertTrue : BOOL
VAR_INPUT
    sName : STRING(80);
    xCond : BOOL;
END_VAR
// ===== IMPLEMENTATION =====
AssertTrue := Rec(sName, xCond, 'expected TRUE');
