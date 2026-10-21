// PATH: Application/FB_F_Conveyor_Test
// ===== DECLARATION =====
FUNCTION_BLOCK FB_F_Conveyor_Test
VAR
    ass : FB_Assert;
END_VAR
// ===== IMPLEMENTATION =====
IF NOT ass.Begin('Conveyor') THEN
    RETURN;
END_IF
Test_StartRuns();
Test_StopHalts();
Test_EStopWins();
Test_KeepsRunningAfterStartReleased();
Test_StopBeatsStart();
ass.Finish();
