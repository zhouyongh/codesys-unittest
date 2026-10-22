// PATH: Application/Tests/FB_DecideSort_Test/Test_QualityNgPushes
// ===== TEST CASE =====
// name  : Test_QualityNgPushes
// intent: NG piece must be pushed to the reject lane
// steps : 1) call F_DecideSort(TRUE, FALSE)
// expects: result TRUE
// ===== DECLARATION =====
METHOD PUBLIC Test_QualityNgPushes
// ===== IMPLEMENTATION =====
ass.AssertTrue('DecideSort.Test_QualityNgPushes', F_DecideSort(TRUE, FALSE));
