// PATH: Application/FB_F_Diverter_Test/Test_ExtendsAfterDelayThenRetracts
// ===== DECLARATION =====
METHOD PUBLIC Test_ExtendsAfterDelayThenRetracts
VAR
    fb : FB_Diverter;
    i : DINT;
    xSawExtend : BOOL;
    xSawDone : BOOL;
END_VAR
// ===== IMPLEMENTATION =====
// The observation flags are method locals and persist across runs; clear them
// so the assertions below describe THIS run only.
xSawExtend := FALSE;
xSawDone := FALSE;

fb(xTrigger := FALSE, dtMs := 0);
fb(xTrigger := TRUE, dtMs := 10);

// 40 ms into the 50 ms delay: the cylinder must still be retracted.
FOR i := 1 TO 3 DO
    fb(xTrigger := FALSE, dtMs := 10);
    IF fb.xCylinder THEN
        xSawExtend := TRUE;
    END_IF
END_FOR
ass.AssertFalse('Diverter.Test_not_extended_before_delay', fb.xCylinder);

// Run out the rest of the sequence (extend 30 ms, retract 20 ms).
FOR i := 1 TO 9 DO
    fb(xTrigger := FALSE, dtMs := 10);
    IF fb.xCylinder THEN
        xSawExtend := TRUE;
    END_IF
    IF fb.xDone THEN
        xSawDone := TRUE;
    END_IF
END_FOR
ass.AssertTrue('Diverter.Test_extends', xSawExtend);
ass.AssertTrue('Diverter.Test_finishes', xSawDone);
ass.AssertFalse('Diverter.Test_cylinder_retracted', fb.xCylinder);
