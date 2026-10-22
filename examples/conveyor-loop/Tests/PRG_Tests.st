// PATH: Application/Tests/PRG_Tests
// ===== DECLARATION =====
PROGRAM PRG_Tests
VAR
    fbDecide : FB_DecideSort_Test;
    fbDiv : FB_Diverter_Test;
    fbConv : FB_Conveyor_Test;
    fbStats : FB_Stats_Test;
    xRunDecide : BOOL;
    xRunDiv : BOOL;
    xRunConv : BOOL;
    xRunStats : BOOL;
END_VAR
// ===== IMPLEMENTATION =====
// g_sFilter: empty = all suites; 'Diverter' or 'FB_Diverter_Test' = only that
// suite. The total must match the suites actually called, or g_xDone never sets.
xRunDecide := GVL_Test.g_sFilter = '' OR GVL_Test.g_sFilter = 'DecideSort' OR GVL_Test.g_sFilter = 'FB_DecideSort_Test';
xRunDiv := GVL_Test.g_sFilter = '' OR GVL_Test.g_sFilter = 'Diverter' OR GVL_Test.g_sFilter = 'FB_Diverter_Test';
xRunConv := GVL_Test.g_sFilter = '' OR GVL_Test.g_sFilter = 'Conveyor' OR GVL_Test.g_sFilter = 'FB_Conveyor_Test';
xRunStats := GVL_Test.g_sFilter = '' OR GVL_Test.g_sFilter = 'Stats' OR GVL_Test.g_sFilter = 'FB_Stats_Test';

GVL_Test.g_uiSuitesTotal := 0;
IF xRunDecide THEN GVL_Test.g_uiSuitesTotal := GVL_Test.g_uiSuitesTotal + 1; END_IF
IF xRunDiv THEN GVL_Test.g_uiSuitesTotal := GVL_Test.g_uiSuitesTotal + 1; END_IF
IF xRunConv THEN GVL_Test.g_uiSuitesTotal := GVL_Test.g_uiSuitesTotal + 1; END_IF
IF xRunStats THEN GVL_Test.g_uiSuitesTotal := GVL_Test.g_uiSuitesTotal + 1; END_IF

IF xRunDecide THEN fbDecide(); END_IF
IF xRunDiv THEN fbDiv(); END_IF
IF xRunConv THEN fbConv(); END_IF
IF xRunStats THEN fbStats(); END_IF
