// PATH: Application/Tests/FB_Diverter_Test/Test_CountsCompletedPushes
// ===== TEST CASE =====
// name  : Test_CountsCompletedPushes
// intent: each finished sequence increments uiPushCount by one
// steps : 1) record uiPushCount
//         2) one full push sequence
// expects: uiPushCount = before + 1
// ===== DECLARATION =====
METHOD PUBLIC Test_CountsCompletedPushes
VAR
    uiBefore : UINT;
    diAfter : DINT;
    i : DINT;
END_VAR
// ===== IMPLEMENTATION =====
uiBefore := fb.uiPushCount;
fb(xTrigger := FALSE, dtMs := 0);
fb(xTrigger := TRUE, dtMs := 10);
FOR i := 1 TO 12 DO
    fb(xTrigger := FALSE, dtMs := 10);
END_FOR
diAfter := TO_DINT(fb.uiPushCount);
ass.AssertEquals_DINT('Diverter.Test_counts', TO_DINT(uiBefore) + 1, diAfter);
