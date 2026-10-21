// PATH: Application/FB_F_Conveyor_Test/Test_StartRuns
// ===== DECLARATION =====
METHOD PUBLIC Test_StartRuns
VAR
    fb : FB_Conveyor;
END_VAR
// ===== IMPLEMENTATION =====
fb(xStart := FALSE, xStop := FALSE, xEStop := TRUE);
fb(xStart := TRUE, xStop := FALSE, xEStop := TRUE);
ass.AssertTrue('Conveyor.Test_StartRuns', fb.xRun);