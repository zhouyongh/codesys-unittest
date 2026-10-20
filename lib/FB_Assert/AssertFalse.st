// PATH: <Application>/FB_Assert/AssertFalse
// ===== DECLARATION =====
METHOD PUBLIC AssertFalse : BOOL
VAR_INPUT
    sName : STRING(80);
    xCond : BOOL;
END_VAR
// ===== IMPLEMENTATION =====
AssertFalse := Rec(sName, NOT xCond, 'expected FALSE');
