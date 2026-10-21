// PATH: Application/FB_F_Diverter_Test/Test_CountsCompletedPushes
// ===== DECLARATION =====
METHOD PUBLIC Test_CountsCompletedPushes
VAR
    fb : FB_Diverter;
    i : DINT;
    diBase : DINT;
END_VAR
// ===== IMPLEMENTATION =====
// uiPushCount survives a re-login: assert the delta of this run.
fb(xTrigger := FALSE, dtMs := 0);
diBase := TO_DINT(fb.uiPushCount);
fb(xTrigger := TRUE, dtMs := 10);
FOR i := 1 TO 12 DO
    fb(xTrigger := FALSE, dtMs := 10);
END_FOR
ass.AssertEquals_DINT('Diverter.Test_counts', 1, TO_DINT(fb.uiPushCount) - diBase);
