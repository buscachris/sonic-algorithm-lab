; Private lab state in the SAGE engine's unused $B400..$B4FF RAM pocket.
; All addresses refer to the exact parent recorded in BUILD_INFO.json.
v_magic         equ $FFB400
v_version       equ $FFB404
v_room          equ $FFB406 ; 0 hub, 1..12 demonstrations
v_algorithm     equ $FFB408
v_dataset       equ $FFB40A
v_running       equ $FFB40C
v_done          equ $FFB40E
v_phase         equ $FFB410 ; 0 idle, 2 sort compare, 3 exchange, 4 algorithm step
v_timer         equ $FFB412
v_comparisons   equ $FFB414
v_swaps         equ $FFB416
v_outer         equ $FFB418
v_index         equ $FFB41A
v_pass          equ $FFB41C
v_pass_swapped  equ $FFB41E
v_pair_left     equ $FFB420
v_pair_right    equ $FFB422
v_want_swap     equ $FFB424
v_message       equ $FFB426
v_last_left     equ $FFB428
v_last_right    equ $FFB42A
v_operations    equ $FFB42C ; completed/started visible steps
v_state         equ $FFB42E ; algorithm-local state
v_target        equ $FFB430
v_low           equ $FFB432 ; binary low / BFS queue head / allocation request
v_high          equ $FFB434 ; binary high / BFS queue tail
v_mid           equ $FFB436 ; binary mid / BFS node / active job / block cursor
v_event         equ $FFB438
v_result_len    equ $FFB43A
v_auto_delay    equ $FFB43C
v_mask          equ $FFB43E ; BFS discovered nodes / finished jobs
v_values        equ $FFB440
v_ids           equ $FFB448
v_aux           equ $FFB450 ; priorities / requests
v_initial       equ $FFB458 ; original burst lengths
v_completed     equ $FFB460 ; one bit per example; retained on travel
v_gates         equ $FFB462
v_route         equ $FFB464 ; pending: 0 none, 1..12 demonstrations, 13 hub
v_floor         equ $FFB466
v_row_y         equ $FFB468
v_age           equ $FFB46A
v_frames        equ $FFB46C
v_last_action   equ $FFB470
v_action_count  equ $FFB472
v_elapsed       equ $FFB474
v_total_wait    equ $FFB476
v_pending       equ $FFB478
v_result_mask   equ $FFB47A
v_queue         equ $FFB480 ; eight node IDs, FIFO
v_result        equ $FFB488 ; path / completion order / allocation results
v_graph         equ $FFB490 ; eight directed adjacency bitmasks
v_parents       equ $FFB498 ; BFS predecessors / allocation results
v_waits         equ $FFB4A0 ; four word waiting times (A-D)
v_turnaround    equ $FFB4B0 ; four word turnaround times (A-D)
v_min           equ $FFB4C0 ; selection minimum / heap maximum candidate
v_width         equ $FFB4C2 ; bottom-up merge run width
v_base          equ $FFB4C4 ; merge segment start
v_end           equ $FFB4C6 ; merge segment end (exclusive)
v_write         equ $FFB4C8 ; merge buffer cursor
v_pivot         equ $FFB4CA ; quicksort pivot value
v_stack_len     equ $FFB4CC ; quicksort pending ranges
v_heap_size     equ $FFB4CE ; active heap size (exclusive)
v_root          equ $FFB4D0 ; sift-down root
v_child         equ $FFB4D2 ; sift-down child under comparison
v_build         equ $FFB4D4 ; 1 while building the initial heap
v_stack         equ $FFB4E0 ; eight pairs of word bounds; quicksort's stack

AlgorithmCount  equ 12
ActionStep      equ AlgorithmCount
ActionRun       equ AlgorithmCount+1
ActionReset     equ AlgorithmCount+2
ActionInput     equ AlgorithmCount+3
ActionPause     equ AlgorithmCount+4
ReturnRing      equ AlgorithmCount

VDP_DATA        equ $C00000
VDP_CTRL        equ $C00004
Sonic           equ $FFFFD000
Zone            equ $FFFFB2E0
ExecuteObjects  equ $11A70
DisplaySprite   equ $11F0E
SolidObject     equ $14372
SoundEffect     equ $248E
SfxComplete     equ $C5 ; native act-results cash register (parent ROM $10ECA)
LabTile         equ $580
