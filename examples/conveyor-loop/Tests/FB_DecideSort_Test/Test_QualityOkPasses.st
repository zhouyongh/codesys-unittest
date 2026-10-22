// PATH: Application/Tests/FB_DecideSort_Test/Test_QualityOkPasses
// ===== TEST CASE =====
// name  : Test_QualityOkPasses
// intent: good piece continues on the belt (no push)
// steps : 1) call F_DecideSort(TRUE, TRUE)
// expects: result FALSE
// ===== DECLARATION =====
METHOD PUBLIC Test_QualityOkPasses
// ===== IMPLEMENTATION =====
ass.AssertFalse('DecideSort.Test_QualityOkPasses', F_DecideSort(TRUE, TRUE));
