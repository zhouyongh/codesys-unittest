// PATH: Application/FB_F_Stats_Test/Test_CountsPassAndReject
// ===== DECLARATION =====
METHOD PUBLIC Test_CountsPassAndReject
VAR
    fb : FB_Stats;
END_VAR
// ===== IMPLEMENTATION =====
fb(xCountPass := TRUE, xCountReject := FALSE);
fb(xCountPass := FALSE, xCountReject := FALSE);
fb(xCountPass := FALSE, xCountReject := TRUE);
fb(xCountPass := FALSE, xCountReject := FALSE);
ass.AssertEquals_DINT('Stats.Test_pass', 1, TO_DINT(fb.uiPass));
ass.AssertEquals_DINT('Stats.Test_reject', 1, TO_DINT(fb.uiReject));
ass.AssertEquals_DINT('Stats.Test_total', 2, TO_DINT(fb.uiTotal));