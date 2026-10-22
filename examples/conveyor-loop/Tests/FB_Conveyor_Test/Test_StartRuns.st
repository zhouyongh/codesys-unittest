// PATH: Application/Tests/FB_Conveyor_Test/Test_StartRuns
// ===== TEST CASE =====
// name  : Test_StartRuns
// intent: start request with e-stop released runs the belt
// steps : 1) force stopped
//         2) xStart TRUE
// expects: xRun TRUE
// ===== DECLARATION =====
METHOD PUBLIC Test_StartRuns
// ===== IMPLEMENTATION =====
fb(xStart := FALSE, xStop := TRUE, xEStop := TRUE);
fb(xStart := TRUE, xStop := FALSE, xEStop := TRUE);
ass.AssertTrue('Conveyor.Test_StartRuns', fb.xRun);
