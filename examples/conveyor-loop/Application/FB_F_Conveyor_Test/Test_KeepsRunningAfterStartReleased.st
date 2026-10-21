// PATH: Application/FB_F_Conveyor_Test/Test_KeepsRunningAfterStartReleased
// ===== DECLARATION =====
METHOD PUBLIC Test_KeepsRunningAfterStartReleased
VAR
    fb : FB_Conveyor;
END_VAR
// ===== IMPLEMENTATION =====
fb(xStart := FALSE, xStop := TRUE, xEStop := TRUE);   // force stopped
fb(xStart := TRUE, xStop := FALSE, xEStop := TRUE);   // start
fb(xStart := FALSE, xStop := FALSE, xEStop := TRUE);  // release start
ass.AssertTrue('Conveyor.Test_keeps_running', fb.xRun);
