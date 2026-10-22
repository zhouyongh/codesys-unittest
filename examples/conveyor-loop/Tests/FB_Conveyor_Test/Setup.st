// PATH: Application/Tests/FB_Conveyor_Test/Setup
// ===== TEST CASE =====
// name  : Setup
// intent: e-stop released, belt stopped
// steps : 1) call fb with all requests FALSE and xEStop TRUE
// expects: xRun FALSE
// ===== DECLARATION =====
METHOD PUBLIC Setup
// ===== IMPLEMENTATION =====
fb(xStart := FALSE, xStop := FALSE, xEStop := TRUE);
