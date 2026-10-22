// PATH: Application/Tests/FB_Diverter_Test
// ===== TEST SUITE =====
// unit   : FB_Diverter
// purpose: one-shot diverter (delay / extend / retract) and push count
// cases  : Test_DoesNotPushWhenIdle
//          Test_ExtendsAfterDelayThenRetracts
//          Test_CountsCompletedPushes
// fixture: Setup builds a fresh fb; TearDown clears trigger
// tags   : unit, timing
// ===== DECLARATION =====
FUNCTION_BLOCK FB_Diverter_Test
VAR
    ass : FB_Assert;
    fb : FB_Diverter;
END_VAR
// ===== IMPLEMENTATION =====
IF NOT ass.Begin('Diverter') THEN
    RETURN;
END_IF
Setup();
Test_DoesNotPushWhenIdle();
TearDown();
Setup();
Test_ExtendsAfterDelayThenRetracts();
TearDown();
Setup();
Test_CountsCompletedPushes();
TearDown();
ass.Finish();
