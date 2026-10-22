// PATH: Application/Tests/FB_Stats_Test/Test_EdgesOnly
// ===== TEST CASE =====
// name  : Test_EdgesOnly
// intent: a held input must not count twice
// steps : 1) drive low, record baseline
//         2) xCountPass TRUE for two consecutive calls
// expects: uiPass increases by one (delta)
// ===== DECLARATION =====
METHOD PUBLIC Test_EdgesOnly
VAR
    uiPass0 : UINT;
    diActual : DINT;
END_VAR
// ===== IMPLEMENTATION =====
fb(xCountPass := FALSE, xCountReject := FALSE);
uiPass0 := fb.uiPass;
fb(xCountPass := TRUE, xCountReject := FALSE);
fb(xCountPass := TRUE, xCountReject := FALSE);
diActual := TO_DINT(fb.uiPass) - TO_DINT(uiPass0);
ass.AssertEquals_DINT('Stats.Test_edges_only', 1, diActual);
