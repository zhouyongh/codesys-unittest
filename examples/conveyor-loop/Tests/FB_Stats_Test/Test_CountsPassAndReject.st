// PATH: Application/Tests/FB_Stats_Test/Test_CountsPassAndReject
// ===== TEST CASE =====
// name  : Test_CountsPassAndReject
// intent: one pass and one reject update all three counters
// steps : 1) drive inputs low, record the baseline
//         2) pass edge, idle, reject edge, idle
// expects: uiPass/uiReject +1, uiTotal +2 (delta, repeat-run safe)
// ===== DECLARATION =====
METHOD PUBLIC Test_CountsPassAndReject
VAR
    uiPass0 : UINT;
    uiReject0 : UINT;
    uiTotal0 : UINT;
END_VAR
// ===== IMPLEMENTATION =====
fb(xCountPass := FALSE, xCountReject := FALSE);
uiPass0 := fb.uiPass;
uiReject0 := fb.uiReject;
uiTotal0 := fb.uiTotal;
fb(xCountPass := TRUE, xCountReject := FALSE);
fb(xCountPass := FALSE, xCountReject := FALSE);
fb(xCountPass := FALSE, xCountReject := TRUE);
fb(xCountPass := FALSE, xCountReject := FALSE);
ass.AssertEquals_DINT('Stats.Test_pass', 1, TO_DINT(fb.uiPass) - TO_DINT(uiPass0));
ass.AssertEquals_DINT('Stats.Test_reject', 1, TO_DINT(fb.uiReject) - TO_DINT(uiReject0));
ass.AssertEquals_DINT('Stats.Test_total', 2, TO_DINT(fb.uiTotal) - TO_DINT(uiTotal0));
