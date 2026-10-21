// PATH: Application/FB_F_Stats_Test/Test_CountsPassAndReject
// ===== DECLARATION =====
METHOD PUBLIC Test_CountsPassAndReject
VAR
    fb : FB_Stats;
    diPass0 : DINT;
    diReject0 : DINT;
    diTotal0 : DINT;
END_VAR
// ===== IMPLEMENTATION =====
// Counters live in the method-local FB and survive a re-login, so assert the
// delta of this run instead of an absolute value. Two runs in a row stay green.
fb(xCountPass := FALSE, xCountReject := FALSE);
diPass0 := TO_DINT(fb.uiPass);
diReject0 := TO_DINT(fb.uiReject);
diTotal0 := TO_DINT(fb.uiTotal);
fb(xCountPass := TRUE, xCountReject := FALSE);
fb(xCountPass := FALSE, xCountReject := FALSE);
fb(xCountPass := FALSE, xCountReject := TRUE);
fb(xCountPass := FALSE, xCountReject := FALSE);
ass.AssertEquals_DINT('Stats.Test_pass', 1, TO_DINT(fb.uiPass) - diPass0);
ass.AssertEquals_DINT('Stats.Test_reject', 1, TO_DINT(fb.uiReject) - diReject0);
ass.AssertEquals_DINT('Stats.Test_total', 2, TO_DINT(fb.uiTotal) - diTotal0);
