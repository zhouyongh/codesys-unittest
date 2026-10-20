// PATH: <Application>/FB_F_Clamp_Test
// ===== DECLARATION =====
FUNCTION_BLOCK FB_F_Clamp_Test
VAR
    ass : FB_Assert;
    R_LOW : LREAL := 2.0;
    R_HIGH : LREAL := 10.0;
    R_INSIDE : LREAL := 5.0;
    R_BELOW : LREAL := -3.0;
    R_ABOVE : LREAL := 12.5;
END_VAR
// ===== IMPLEMENTATION =====
IF NOT ass.Begin('F_Clamp') THEN
    RETURN;
END_IF
Test_InsideRangeReturnsValue();
Test_BelowLowReturnsLow();
Test_AboveHighReturnsHigh();
Test_EqualBoundsReturnsBound();
Test_LowGreaterThanHighSwapsBounds();
ass.Finish();