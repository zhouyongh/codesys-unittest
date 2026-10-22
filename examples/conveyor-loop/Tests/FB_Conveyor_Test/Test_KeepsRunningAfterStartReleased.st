// PATH: Application/Tests/FB_Conveyor_Test/Test_KeepsRunningAfterStartReleased
// ===== TEST CASE =====
// name  : Test_KeepsRunningAfterStartReleased
// intent: start is a command edge; belt stays on after the button is released
// steps : 1) force stopped, then start
//         2) xStart FALSE
// expects: xRun TRUE
// ===== DECLARATION =====
METHOD PUBLIC Test_KeepsRunningAfterStartReleased
// ===== IMPLEMENTATION =====
fb(xStart := FALSE, xStop := TRUE, xEStop := TRUE);
fb(xStart := TRUE, xStop := FALSE, xEStop := TRUE);
fb(xStart := FALSE, xStop := FALSE, xEStop := TRUE);
ass.AssertTrue('Conveyor.Test_KeepsRunningAfterStartReleased', fb.xRun);
