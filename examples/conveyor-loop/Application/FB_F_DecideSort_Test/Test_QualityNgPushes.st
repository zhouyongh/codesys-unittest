// PATH: Application/FB_F_DecideSort_Test/Test_QualityNgPushes
// ===== DECLARATION =====
METHOD PUBLIC Test_QualityNgPushes
// ===== IMPLEMENTATION =====
ass.AssertTrue('DecideSort.Test_QualityNgPushes',
    F_DecideSort(TRUE, FALSE));