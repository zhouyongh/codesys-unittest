// PATH: <Application>/F_Clamp
// ===== DECLARATION =====
FUNCTION F_Clamp : LREAL
VAR_INPUT
    lrValue : LREAL;
    lrLow : LREAL;
    lrHigh : LREAL;
END_VAR
VAR
    lrLo : LREAL;
    lrHi : LREAL;
END_VAR
// ===== IMPLEMENTATION =====
lrLo := lrLow;
lrHi := lrHigh;
IF lrLo > lrHi THEN
    lrLo := lrHigh;
    lrHi := lrLow;
END_IF
IF lrValue < lrLo THEN
    F_Clamp := lrLo;
ELSIF lrValue > lrHi THEN
    F_Clamp := lrHi;
ELSE
    F_Clamp := lrValue;
END_IF