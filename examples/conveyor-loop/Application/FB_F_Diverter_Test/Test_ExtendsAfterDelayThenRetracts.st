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
fb(xTrigger := FALSE, dtMs := 0);
fb(xTrigger := TRUE, dtMs := 10);
FOR i := 1 TO 12 DO
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