// PATH: Application/FB_F_Stats_Test
// ===== DECLARATION =====
FUNCTION_BLOCK FB_F_Stats_Test
VAR
    ass : FB_Assert;
END_VAR
// ===== IMPLEMENTATION =====
IF NOT ass.Begin('Stats') THEN
    RETURN;
END_IF
Test_CountsPassAndReject();
Test_EdgesOnly();
ass.Finish();