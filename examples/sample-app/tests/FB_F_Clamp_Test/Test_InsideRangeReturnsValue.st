// PATH: Application/FB_F_Clamp_Test/Test_InsideRangeReturnsValue
// ===== DECLARATION =====
METHOD PUBLIC Test_InsideRangeReturnsValue
// ===== IMPLEMENTATION =====
ass.AssertEquals_LREAL('F_Clamp.Test_InsideRangeReturnsValue',
    R_INSIDE, F_Clamp(R_INSIDE, R_LOW, R_HIGH), 0.0);
