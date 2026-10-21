// PATH: Application/FB_F_Clamp_Test/Test_AboveHighReturnsHigh
// ===== DECLARATION =====
METHOD PUBLIC Test_AboveHighReturnsHigh
// ===== IMPLEMENTATION =====
ass.AssertEquals_LREAL('F_Clamp.Test_AboveHighReturnsHigh',
    R_HIGH, F_Clamp(R_ABOVE, R_LOW, R_HIGH), 0.0);
