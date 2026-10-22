// PATH: Application/Tests/FB_Diverter_Test/Test_DoesNotPushWhenIdle
// ===== TEST CASE =====
// name  : Test_DoesNotPushWhenIdle
// intent: no trigger -> cylinder stays in, not busy
// steps : 1) fb already in default state (Setup)
//         2) call fb once with xTrigger FALSE
// expects: xCylinder = FALSE, xBusy = FALSE
// ===== DECLARATION =====
METHOD PUBLIC Test_DoesNotPushWhenIdle
// ===== IMPLEMENTATION =====
fb(xTrigger := FALSE, dtMs := 10);
ass.AssertFalse('Diverter.Test_DoesNotPushWhenIdle', fb.xCylinder);
ass.AssertFalse('Diverter.Test_DoesNotPushWhenIdle_busy', fb.xBusy);
