// PATH: Application/FB_F_Stats_Test/Test_EdgesOnly
// ===== DECLARATION =====
METHOD PUBLIC Test_EdgesOnly
VAR
    fb : FB_Stats;
    diBase : DINT;
END_VAR
// ===== IMPLEMENTATION =====
// Drive low first so the next TRUE is a real rising edge even on a second run.
fb(xCountPass := FALSE, xCountReject := FALSE);
diBase := TO_DINT(fb.uiPass);
fb(xCountPass := TRUE, xCountReject := FALSE);
fb(xCountPass := TRUE, xCountReject := FALSE);
ass.AssertEquals_DINT('Stats.Test_edges_only', 1, TO_DINT(fb.uiPass) - diBase);
