// PATH: Application/Tests/FB_Conveyor_Test/Test_StopBeatsStart
// ===== TEST CASE =====
// name  : Test_StopBeatsStart
// intent: simultaneous stop and start keeps the belt stopped
// steps : 1) xStart and xStop both TRUE
// expects: xRun FALSE
// ===== DECLARATION =====
METHOD PUBLIC Test_StopBeatsStart
// ===== IMPLEMENTATION =====
fb(xStart := TRUE, xStop := TRUE, xEStop := TRUE);
ass.AssertFalse('Conveyor.Test_StopBeatsStart', fb.xRun);
