// PATH: Application/Tests/FB_Conveyor_Test/TearDown
// ===== TEST CASE =====
// name  : TearDown
// intent: force belt off after each case
// steps : 1) xStop TRUE
// expects: xRun FALSE
// ===== DECLARATION =====
METHOD PUBLIC TearDown
// ===== IMPLEMENTATION =====
fb(xStart := FALSE, xStop := TRUE, xEStop := TRUE);
