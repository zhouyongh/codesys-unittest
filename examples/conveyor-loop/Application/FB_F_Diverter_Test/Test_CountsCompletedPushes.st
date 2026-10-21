// PATH: Application/FB_F_Diverter_Test/Test_CountsCompletedPushes
// ===== DECLARATION =====
METHOD PUBLIC Test_CountsCompletedPushes
VAR
    fb : FB_Diverter;
    i : DINT;
    diAfter : DINT;
END_VAR
// ===== IMPLEMENTATION =====
fb(xTrigger := FALSE, dtMs := 0);
fb(xTrigger := TRUE, dtMs := 10);
FOR i := 1 TO 12 DO
    fb(xTrigger := FALSE, dtMs := 10);
END_FOR
diAfter := TO_DINT(fb.uiPushCount);
ass.AssertEquals_DINT('Diverter.Test_counts', 1, diAfter);