// PATH: Application/Tests/FB_Conveyor_Test
// ===== TEST SUITE =====
// unit   : FB_Conveyor
// purpose: belt run/stop interlocks; e-stop always wins
// cases  : Test_StartRuns
//          Test_StopHalts
//          Test_EStopWins
//          Test_KeepsRunningAfterStartReleased
//          Test_StopBeatsStart
// fixture: Setup defaults xEStop released; TearDown stops belt
// tags   : unit, interlock
// ===== DECLARATION =====
FUNCTION_BLOCK FB_Conveyor_Test
VAR
    ass : FB_Assert;
    fb : FB_Conveyor;
END_VAR
// ===== IMPLEMENTATION =====
IF NOT ass.Begin('Conveyor') THEN
    RETURN;
END_IF
Setup();
Test_StartRuns();
TearDown();
Setup();
Test_StopHalts();
TearDown();
Setup();
Test_EStopWins();
TearDown();
Setup();
Test_KeepsRunningAfterStartReleased();
TearDown();
Setup();
Test_StopBeatsStart();
TearDown();
ass.Finish();
