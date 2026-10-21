// PATH: Application/FB_F_Diverter_Test
// ===== DECLARATION =====
FUNCTION_BLOCK FB_F_Diverter_Test
VAR
    ass : FB_Assert;
END_VAR
// ===== IMPLEMENTATION =====
IF NOT ass.Begin('Diverter') THEN
    RETURN;
END_IF
Test_DoesNotPushWhenIdle();
Test_ExtendsAfterDelayThenRetracts();
Test_CountsCompletedPushes();
ass.Finish();