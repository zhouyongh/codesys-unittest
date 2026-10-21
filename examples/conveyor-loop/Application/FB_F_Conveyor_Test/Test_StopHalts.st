// PATH: Application/FB_F_Conveyor_Test/Test_StopHalts
// ===== DECLARATION =====
METHOD PUBLIC Test_StopHalts
VAR
    fb : FB_Conveyor;
END_VAR
// ===== IMPLEMENTATION =====
fb(xStart := TRUE, xStop := FALSE, xEStop := TRUE);
fb(xStart := FALSE, xStop := TRUE, xEStop := TRUE);
ass.AssertFalse('Conveyor.Test_StopHalts', fb.xRun);