// PATH: Application/FB_F_Clamp_Test/Test_EqualBoundsReturnsBound
// ===== DECLARATION =====
METHOD PUBLIC Test_EqualBoundsReturnsBound
// ===== IMPLEMENTATION =====
ass.AssertEquals_LREAL('F_Clamp.Test_EqualBoundsReturnsBound',
    4.0, F_Clamp(99.0, 4.0, 4.0), 0.0);
