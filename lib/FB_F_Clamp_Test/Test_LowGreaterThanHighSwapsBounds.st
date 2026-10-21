// PATH: Application/FB_F_Clamp_Test/Test_LowGreaterThanHighSwapsBounds
// ===== DECLARATION =====
METHOD PUBLIC Test_LowGreaterThanHighSwapsBounds
// ===== IMPLEMENTATION =====
ass.AssertEquals_LREAL('F_Clamp.Test_LowGreaterThanHighSwapsBounds',
    R_LOW, F_Clamp(1.0, R_HIGH, R_LOW), 0.0);
