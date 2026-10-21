// PATH: Application/FB_F_DecideSort_Test/Test_NoPieceNeverPushes
// ===== DECLARATION =====
METHOD PUBLIC Test_NoPieceNeverPushes
// ===== IMPLEMENTATION =====
ass.AssertFalse('DecideSort.Test_NoPieceNeverPushes',
    F_DecideSort(FALSE, FALSE));