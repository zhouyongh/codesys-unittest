// PATH: Application/FB_F_Diverter_Test/Test_DoesNotPushWhenIdle
// ===== DECLARATION =====
METHOD PUBLIC Test_DoesNotPushWhenIdle
VAR
    fb : FB_Diverter;
END_VAR
// ===== IMPLEMENTATION =====
fb(xTrigger := FALSE, dtMs := 10);
ass.AssertFalse('Diverter.Test_DoesNotPushWhenIdle', fb.xCylinder);
ass.AssertFalse('Diverter.Test_DoesNotPushWhenIdle_busy', fb.xBusy);