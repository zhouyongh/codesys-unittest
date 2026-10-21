// PATH: Application/FB_Conveyor
// ===== DECLARATION =====
FUNCTION_BLOCK FB_Conveyor
VAR_INPUT
    xStart : BOOL;                // start request
    xStop : BOOL;                 // stop request (falling priority under run)
    xEStop : BOOL;                // emergency stop, NC-style TRUE = released
END_VAR
VAR_OUTPUT
    xRun : BOOL;
END_VAR
// ===== IMPLEMENTATION =====
// xEStop TRUE = OK (released); FALSE = e-stop pressed
IF NOT xEStop THEN
    xRun := FALSE;
ELSIF xStop THEN
    xRun := FALSE;
ELSIF xStart THEN
    xRun := TRUE;
END_IF
