// PATH: Application/PRG_Tests
// ===== DECLARATION =====
PROGRAM PRG_Tests
VAR
    fbDecide : FB_F_DecideSort_Test;
    fbDiv : FB_F_Diverter_Test;
    fbConv : FB_F_Conveyor_Test;
    fbStats : FB_F_Stats_Test;
END_VAR
// ===== IMPLEMENTATION =====
GVL_Test.g_uiSuitesTotal := 4;
fbDecide();
fbDiv();
fbConv();
fbStats();
