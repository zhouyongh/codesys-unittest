// PATH: Application/FB_Stats
// ===== DECLARATION =====
FUNCTION_BLOCK FB_Stats
VAR_INPUT
    xCountPass : BOOL;            // rising edge: one OK piece
    xCountReject : BOOL;          // rising edge: one NG piece
END_VAR
VAR_OUTPUT
    uiPass : UINT;
    uiReject : UINT;
    uiTotal : UINT;
END_VAR
VAR
    xPassPrev : BOOL;
    xRejPrev : BOOL;
END_VAR
// ===== IMPLEMENTATION =====
IF xCountPass AND NOT xPassPrev THEN
    uiPass := uiPass + 1;
    uiTotal := uiTotal + 1;
END_IF
IF xCountReject AND NOT xRejPrev THEN
    uiReject := uiReject + 1;
    uiTotal := uiTotal + 1;
END_IF
xPassPrev := xCountPass;
xRejPrev := xCountReject;
