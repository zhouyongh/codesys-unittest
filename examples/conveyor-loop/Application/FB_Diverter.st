// PATH: Application/FB_Diverter
// ===== DECLARATION =====
FUNCTION_BLOCK FB_Diverter
VAR CONSTANT
    PUSH_DELAY_MS : DINT := 50;   // wait after trigger before extending
    EXTEND_MS : DINT := 30;       // cylinder out
    RETRACT_MS : DINT := 20;      // cylinder back
END_VAR
VAR_INPUT
    xTrigger : BOOL;              // rising edge = start one push
    dtMs : DINT;                  // elapsed time of this call (test-friendly)
END_VAR
VAR_OUTPUT
    xCylinder : BOOL;             // cylinder out
    xBusy : BOOL;                 // sequence running
    xDone : BOOL;                 // one-shot: sequence finished
    uiPushCount : UINT;           // completed pushes
END_VAR
VAR
    xTrigPrev : BOOL;
    diPhase : DINT;               // 0 idle, 1 delay, 2 extend, 3 retract
    diElapsed : DINT;
END_VAR
// ===== IMPLEMENTATION =====
// rising edge triggers a cycle only when idle
IF xTrigger AND NOT xTrigPrev AND diPhase = 0 THEN
    diPhase := 1;
    diElapsed := 0;
    xBusy := TRUE;
    xDone := FALSE;
END_IF
xTrigPrev := xTrigger;

IF diPhase > 0 THEN
    diElapsed := diElapsed + dtMs;
    IF diPhase = 1 THEN
        xCylinder := FALSE;
        IF diElapsed >= PUSH_DELAY_MS THEN
            diPhase := 2;
            diElapsed := 0;
        END_IF
    ELSIF diPhase = 2 THEN
        xCylinder := TRUE;
        IF diElapsed >= EXTEND_MS THEN
            diPhase := 3;
            diElapsed := 0;
        END_IF
    ELSIF diPhase = 3 THEN
        xCylinder := FALSE;
        IF diElapsed >= RETRACT_MS THEN
            diPhase := 0;
            xBusy := FALSE;
            xDone := TRUE;
            uiPushCount := uiPushCount + 1;
        END_IF
    END_IF
ELSE
    xCylinder := FALSE;
END_IF
