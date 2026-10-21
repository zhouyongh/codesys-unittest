// PATH: Application/FB_F_Stats_Test/Test_EdgesOnly
// ===== DECLARATION =====
METHOD PUBLIC Test_EdgesOnly
VAR
    fb : FB_Stats;
    diActual : DINT;
END_VAR
// ===== IMPLEMENTATION =====
fb(xCountPass := TRUE, xCountReject := FALSE);
fb(xCountPass := TRUE, xCountReject := FALSE);
diActual := TO_DINT(fb.uiPass);
ass.AssertEquals_DINT('Stats.Test_edges_only', 1, diActual);