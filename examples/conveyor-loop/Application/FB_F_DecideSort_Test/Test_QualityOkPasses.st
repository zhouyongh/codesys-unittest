// PATH: Application/FB_F_DecideSort_Test/Test_QualityOkPasses
// ===== DECLARATION =====
METHOD PUBLIC Test_QualityOkPasses
// ===== IMPLEMENTATION =====
ass.AssertFalse('DecideSort.Test_QualityOkPasses',
    F_DecideSort(TRUE, TRUE));