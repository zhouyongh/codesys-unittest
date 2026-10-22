// PATH: Application/Tests/FB_DecideSort_Test
// ===== TEST SUITE =====
// unit   : F_DecideSort
// purpose: quality gate decides pass or push-to-reject
// cases  : Test_NoPieceNeverPushes
//          Test_QualityOkPasses
//          Test_QualityNgPushes
// fixture: pure function, no state; Setup clears locals
// tags   : unit
// ===== DECLARATION =====
FUNCTION_BLOCK FB_DecideSort_Test
VAR
    ass : FB_Assert;
END_VAR
// ===== IMPLEMENTATION =====
IF NOT ass.Begin('DecideSort') THEN
    RETURN;
END_IF
Setup();
Test_NoPieceNeverPushes();
TearDown();
Setup();
Test_QualityOkPasses();
TearDown();
Setup();
Test_QualityNgPushes();
TearDown();
ass.Finish();
