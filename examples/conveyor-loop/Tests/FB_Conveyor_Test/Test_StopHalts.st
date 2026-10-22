// PATH: Application/Tests/FB_Conveyor_Test/Test_StopHalts
// ===== TEST CASE =====
// name  : Test_StopHalts
// intent: stop request halts a running belt
// steps : 1) start
//         2) stop
// expects: xRun FALSE
// ===== DECLARATION =====
METHOD PUBLIC Test_StopHalts
// ===== IMPLEMENTATION =====
fb(xStart := TRUE, xStop := FALSE, xEStop := TRUE);
fb(xStart := FALSE, xStop := TRUE, xEStop := TRUE);
ass.AssertFalse('Conveyor.Test_StopHalts', fb.xRun);
