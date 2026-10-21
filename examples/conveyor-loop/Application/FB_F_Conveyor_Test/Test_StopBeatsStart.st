// PATH: Application/FB_F_Conveyor_Test/Test_StopBeatsStart
// ===== DECLARATION =====
METHOD PUBLIC Test_StopBeatsStart
VAR
    fb : FB_Conveyor;
END_VAR
// ===== IMPLEMENTATION =====
fb(xStart := TRUE, xStop := FALSE, xEStop := TRUE);
fb(xStart := TRUE, xStop := TRUE, xEStop := TRUE);
ass.AssertFalse('Conveyor.Test_stop_beats_start', fb.xRun);
