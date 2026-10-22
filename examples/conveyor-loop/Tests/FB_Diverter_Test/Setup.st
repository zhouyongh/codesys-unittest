// PATH: Application/Tests/FB_Diverter_Test/Setup
// ===== TEST CASE =====
// name  : Setup
// intent: fresh diverter instance defaults before each case
// steps : 1) call fb idle once
// expects: internal state idle (no push)
// ===== DECLARATION =====
METHOD PUBLIC Setup
// ===== IMPLEMENTATION =====
fb(xTrigger := FALSE, dtMs := 0);
