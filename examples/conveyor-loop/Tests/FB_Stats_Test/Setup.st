// PATH: Application/Tests/FB_Stats_Test/Setup
// ===== TEST CASE =====
// name  : Setup
// intent: zero counters before each case
// steps : 1) call fb with both inputs FALSE
// expects: no edge
// ===== DECLARATION =====
METHOD PUBLIC Setup
// ===== IMPLEMENTATION =====
fb(xCountPass := FALSE, xCountReject := FALSE);
