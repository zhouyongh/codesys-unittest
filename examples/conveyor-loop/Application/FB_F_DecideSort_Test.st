// PATH: Application/FB_F_DecideSort_Test
// ===== DECLARATION =====
FUNCTION_BLOCK FB_F_DecideSort_Test
VAR
    ass : FB_Assert;
END_VAR
// ===== IMPLEMENTATION =====
IF NOT ass.Begin('DecideSort') THEN
    RETURN;
END_IF
Test_NoPieceNeverPushes();
Test_QualityOkPasses();
Test_QualityNgPushes();
ass.Finish();
