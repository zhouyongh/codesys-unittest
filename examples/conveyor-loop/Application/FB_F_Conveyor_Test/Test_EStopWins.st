// PATH: Application/FB_F_Conveyor_Test/Test_EStopWins
// ===== DECLARATION =====
METHOD PUBLIC Test_EStopWins
VAR
    fb : FB_Conveyor;
END_VAR
// ===== IMPLEMENTATION =====
fb(xStart := TRUE, xStop := FALSE, xEStop := TRUE);
fb(xStart := TRUE, xStop := FALSE, xEStop := FALSE);
ass.AssertFalse('Conveyor.Test_EStopWins', fb.xRun);