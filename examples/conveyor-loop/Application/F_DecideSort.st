// PATH: Application/F_DecideSort
// ===== DECLARATION =====
FUNCTION F_DecideSort : BOOL
VAR_INPUT
    xPiecePresent : BOOL;   // sensor saw a piece
    xQualityOK : BOOL;      // quality sensor: TRUE = OK
END_VAR
// ===== IMPLEMENTATION =====
// no piece: never push
// quality OK: let it pass
// quality NG: push to reject lane
IF NOT xPiecePresent THEN
    F_DecideSort := FALSE;
ELSE
    F_DecideSort := NOT xQualityOK;
END_IF
