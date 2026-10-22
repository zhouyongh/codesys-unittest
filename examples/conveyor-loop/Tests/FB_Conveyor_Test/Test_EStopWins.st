// PATH: Application/Tests/FB_Conveyor_Test/Test_EStopWins
// ===== TEST CASE =====
// name  : Test_EStopWins
// intent: pressed e-stop overrides a start request
// steps : 1) start with e-stop released
//         2) press e-stop while start stays TRUE
// expects: xRun FALSE
// ===== DECLARATION =====
METHOD PUBLIC Test_EStopWins
// ===== IMPLEMENTATION =====
fb(xStart := TRUE, xStop := FALSE, xEStop := TRUE);
fb(xStart := TRUE, xStop := FALSE, xEStop := FALSE);
ass.AssertFalse('Conveyor.Test_EStopWins', fb.xRun);
