// PATH: Application/Tests/FB_Stats_Test/TearDown
// ===== TEST CASE =====
// name  : TearDown
// intent: drop any held edge into the next case
// steps : 1) both inputs FALSE
// expects: no edge
// ===== DECLARATION =====
METHOD PUBLIC TearDown
// ===== IMPLEMENTATION =====
fb(xCountPass := FALSE, xCountReject := FALSE);
