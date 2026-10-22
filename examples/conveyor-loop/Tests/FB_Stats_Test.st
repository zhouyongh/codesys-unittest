// PATH: Application/Tests/FB_Stats_Test
// ===== TEST SUITE =====
// unit   : FB_Stats
// purpose: edge counters for pass / reject / total
// cases  : Test_CountsPassAndReject
//          Test_EdgesOnly
// fixture: Setup builds a fresh fb; TearDown clears inputs
// tags   : unit
// ===== DECLARATION =====
FUNCTION_BLOCK FB_Stats_Test
VAR
    ass : FB_Assert;
    fb : FB_Stats;
END_VAR
// ===== IMPLEMENTATION =====
IF NOT ass.Begin('Stats') THEN
    RETURN;
END_IF
Setup();
Test_CountsPassAndReject();
TearDown();
Setup();
Test_EdgesOnly();
TearDown();
ass.Finish();
