// PATH: Application/Tests/FB_Diverter_Test/TearDown
// ===== TEST CASE =====
// name  : TearDown
// intent: clear trigger so the next case starts clean
// steps : 1) force xTrigger FALSE
// expects: no rising edge into the next case
// ===== DECLARATION =====
METHOD PUBLIC TearDown
// ===== IMPLEMENTATION =====
fb(xTrigger := FALSE, dtMs := 0);
