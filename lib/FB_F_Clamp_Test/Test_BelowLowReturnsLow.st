// PATH: Application/FB_F_Clamp_Test/Test_BelowLowReturnsLow
// ===== DECLARATION =====
METHOD PUBLIC Test_BelowLowReturnsLow
// ===== IMPLEMENTATION =====
ass.AssertEquals_LREAL('F_Clamp.Test_BelowLowReturnsLow',
    R_LOW, F_Clamp(R_BELOW, R_LOW, R_HIGH), 0.0);
