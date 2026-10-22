// PATH: Application/Tests/FB_DecideSort_Test/Test_NoPieceNeverPushes
// ===== TEST CASE =====
// name  : Test_NoPieceNeverPushes
// intent: without a piece the pusher must stay idle
// steps : 1) call F_DecideSort(FALSE, FALSE)
// expects: result FALSE
// ===== DECLARATION =====
METHOD PUBLIC Test_NoPieceNeverPushes
// ===== IMPLEMENTATION =====
ass.AssertFalse('DecideSort.Test_NoPieceNeverPushes', F_DecideSort(FALSE, FALSE));
