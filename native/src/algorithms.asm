; All twelve algorithms execute on the 68000. No recorded answer sequences.
; A step first displays the operation, then commits it after 36 frames.
ResetWorld:
        lea v_running,a0
        moveq #25,d0
.clear:
        clr.w (a0)+
        dbf d0,.clear
        lea v_values,a0
        moveq #7,d0
.arrays:
        clr.l (a0)+
        dbf d0,.arrays
        clr.l v_elapsed
        clr.l v_pending
        lea v_queue,a0
        moveq #13,d0
.work:
        move.l #-1,(a0)+
        dbf d0,.work
        lea v_min,a0
        moveq #15,d0
.scratch:
        clr.l (a0)+
        dbf d0,.scratch
        lea v_ids,a0
        moveq #0,d0
.ids:
        move.b d0,(a0)+
        addq.w #1,d0
        cmpi.w #8,d0
        blo.s .ids
        move.w #-1,v_pair_left
        move.w #-1,v_pair_right
        move.w #-1,v_mid
        move.w #-1,v_pending
        move.w v_algorithm,d0
        cmpi.w #2,d0
        beq.w ResetBinary
        cmpi.w #3,d0
        beq.w ResetBFS
        cmpi.w #4,d0
        beq.w ResetPriority
        cmpi.w #5,d0
        beq.w ResetFirstFit
        cmpi.w #6,d0
        bhs.w ResetExpanded
        move.w #1,v_pass
        move.w #7,v_outer
        tst.w d0
        beq.s .copy_input
        move.w #1,v_outer
        move.w #1,v_index
.copy_input:
CopySortInput:
        lea SortData(pc),a0
        move.w v_dataset,d0
        lsl.w #3,d0
        adda.w d0,a0
CopyEightValues:
        lea v_values,a1
        moveq #7,d0
.copy:
        move.b (a0)+,(a1)+
        dbf d0,.copy
        rts

BeginStep:
        tst.w v_done
        bne.w .return
        tst.w v_phase
        bne.w .return
        move.w v_algorithm,d0
        cmpi.w #2,d0
        beq.w BeginBinary
        cmpi.w #3,d0
        beq.w BeginBFS
        cmpi.w #4,d0
        beq.w BeginPriority
        cmpi.w #5,d0
        beq.w BeginFirstFit
        cmpi.w #6,d0
        bhs.w BeginExpanded
        move.w v_index,d0
        tst.w v_algorithm
        bne.s .insertion
        move.w d0,v_pair_left
        addq.w #1,d0
        move.w d0,v_pair_right
        bra.s CompareNow
.insertion:
        move.w d0,v_pair_right
        subq.w #1,d0
        move.w d0,v_pair_left
        bra.s CompareNow
.return:
        rts

CompareNow:
        lea v_values,a0
        move.w v_pair_left,d2
        move.w v_pair_right,d3
        moveq #0,d0
        moveq #0,d1
        move.b (a0,d2.w),d0
        move.b (a0,d3.w),d1
        move.w d0,v_last_left
        move.w d1,v_last_right
        addq.w #1,v_comparisons
        addq.w #1,v_operations
        clr.w v_want_swap
        move.w #3,v_message
        cmp.b d1,d0
        bls.s .keep
        move.w #1,v_want_swap
        move.w #2,v_message
.keep:
        move.w #2,v_phase
        bra.s ShowOperation

ShowStep:
        addq.w #1,v_operations
        move.w #4,v_phase
ShowOperation:
        move.w #36,v_timer
        move.w #$B5,d0
        jmp SoundEffect

UpdateAlgorithm:
        move.w v_phase,d0
        beq.s .ready
        cmpi.w #4,d0
        beq.w .algorithm
        cmpi.w #2,d0
        beq.s .comparison
        addq.w #1,v_timer
        cmpi.w #32,v_timer
        blo.s .return
        lea v_values,a0
        lea v_ids,a1
        move.w v_pair_left,d0
        move.w v_pair_right,d1
        move.b (a0,d0.w),d2
        move.b (a0,d1.w),d3
        move.b d3,(a0,d0.w)
        move.b d2,(a0,d1.w)
        move.b (a1,d0.w),d2
        move.b (a1,d1.w),d3
        move.b d3,(a1,d0.w)
        move.b d2,(a1,d1.w)
        addq.w #1,v_swaps
        bra.w FinishSortOperation
.ready:
        tst.w v_done
        bne.s .return
        tst.w v_running
        beq.s .return
        tst.w v_auto_delay
        beq.w BeginStep
        subq.w #1,v_auto_delay
.return:
        rts
.comparison:
        subq.w #1,v_timer
        bne.s .return
        tst.w v_want_swap
        beq.s FinishSortOperation
        move.w #3,v_phase
        clr.w v_timer
        rts
.algorithm:
        subq.w #1,v_timer
        bne.s .return
        bsr.s FinishVisual
        move.w v_algorithm,d0
        cmpi.w #2,d0
        beq.w CommitBinary
        cmpi.w #3,d0
        beq.w CommitBFS
        cmpi.w #4,d0
        beq.w CommitPriority
        cmpi.w #8,d0
        beq.w CommitMerge
        cmpi.w #11,d0
        beq.w CommitLinear
        bra.w CommitFirstFit

FinishVisual:
        clr.w v_phase
        move.w #-1,v_pair_left
        move.w #-1,v_pair_right
        move.w #12,v_auto_delay
        rts

FinishSortOperation:
        bsr.s FinishVisual
        cmpi.w #6,v_algorithm
        bhs.w AdvanceExpanded
        tst.w v_algorithm
        bne.s AdvanceInsertion
AdvanceBubble:
        tst.w v_want_swap
        beq.s .next
        move.w #1,v_pass_swapped
.next:
        addq.w #1,v_index
        move.w v_index,d0
        cmp.w v_outer,d0
        blo.s .return
        tst.w v_pass_swapped
        beq.s AlgorithmComplete
        subq.w #1,v_outer
        beq.s AlgorithmComplete
        clr.w v_index
        clr.w v_pass_swapped
        addq.w #1,v_pass
.return:
        rts
AdvanceInsertion:
        tst.w v_want_swap
        beq.s .next
        subq.w #1,v_index
        bne.s .return
.next:
        addq.w #1,v_outer
        cmpi.w #8,v_outer
        beq.s AlgorithmComplete
        move.w v_outer,v_index
        move.w v_outer,v_pass
.return:
        rts
AlgorithmComplete:
        move.w #1,v_done
        clr.w v_running
        move.w #4,v_message
        move.w v_algorithm,d0
        move.w v_completed,d1
        bset d0,d1
        move.w d1,v_completed
        move.w #SfxComplete,d0
        jmp SoundEffect

; Binary search: inclusive bounds; floor midpoint; any matching duplicate.
ResetBinary:
        lea BinaryData(pc),a0
        move.w v_dataset,d0
        mulu.w #10,d0
        adda.w d0,a0
        bsr.w CopyEightValues
        moveq #0,d0
        move.b (a0),d0
        move.w d0,v_target
        move.w #7,v_high
        rts
BeginBinary:
        move.w v_low,d0
        add.w v_high,d0
        lsr.w #1,d0
        move.w d0,v_mid
        move.w d0,v_pair_left
        lea v_values,a0
        moveq #0,d1
        move.b (a0,d0.w),d1
        move.w d1,v_last_left
        move.w v_target,v_last_right
        clr.w v_event          ; 0: value < target
        cmp.w v_target,d1
        blo.s .show
        beq.s .found
        move.w #2,v_event      ; 2: value > target
        bra.s .show
.found:
        move.w #1,v_event      ; 1: found
.show:
        addq.w #1,v_comparisons
        bra.w ShowStep
CommitBinary:
        move.w v_mid,d0
        cmpi.w #1,v_event
        beq.s .found
        tst.w v_event
        bne.s .left
        addq.w #1,d0
        move.w d0,v_low
        bra.s .bounds
.left:
        subq.w #1,d0
        move.w d0,v_high
.bounds:
        move.w v_low,d0
        cmp.w v_high,d0
        bgt.w AlgorithmComplete
        rts
.found:
        move.b d0,v_result
        move.w #1,v_result_len
        bset d0,v_result_mask+1
        bra.w AlgorithmComplete

; Breadth-first search: FIFO, neighbors A..H, visited on discovery.
; The monitor numbers are shortest distances; '-' means undiscovered.
ResetBFS:
        lea GraphData(pc),a0
        move.w v_dataset,d0
        lsl.w #3,d0
        adda.w d0,a0
        lea v_graph,a1
        moveq #7,d0
.graph:
        move.b (a0)+,(a1)+
        dbf d0,.graph
        move.l #-1,v_values
        move.l #-1,v_values+4
        clr.b v_values
        clr.b v_parents
        clr.b v_queue
        move.w #1,v_high
        move.w #1,v_mask
        move.w #1,v_swaps       ; discovered count
        move.w #7,v_target
        rts
BeginBFS:
        tst.w v_state
        bne.s .scan
.dequeue:
        move.w v_low,d0
        cmp.w v_high,d0
        bhs.s .empty
        lea v_queue,a0
        moveq #0,d1
        move.b (a0,d0.w),d1
        move.w d1,v_pending
        move.w d1,v_pair_left
        clr.w v_event          ; dequeue
        bra.w ShowStep
.empty:
        move.w #4,v_event      ; unreachable
        bra.w ShowStep
.scan:
        move.w v_mid,d0
        lea v_graph,a0
        moveq #0,d2
        move.b (a0,d0.w),d2
        move.w v_index,d1
.next:
        cmpi.w #8,d1
        bhs.s .scanned
        btst d1,d2
        bne.s .edge
        addq.w #1,d1
        bra.s .next
.scanned:
        clr.w v_state
        bra.s .dequeue
.edge:
        move.w d0,v_pair_left
        move.w d1,v_pair_right
        move.w d1,v_pending
        addq.w #1,d1
        move.w d1,v_index
        move.w v_pending,d1
        move.w #1,v_event      ; already discovered
        btst d1,v_mask+1
        bne.s .show
        move.w #2,v_event      ; discover new neighbor
.show:
        addq.w #1,v_comparisons
        bra.w ShowStep
CommitBFS:
        move.w v_event,d0
        cmpi.w #4,d0
        beq.w AlgorithmComplete
        tst.w d0
        beq.s .pop
        cmpi.w #2,d0
        beq.s .discover
        rts
.pop:
        move.w v_pending,v_mid
        addq.w #1,v_low
        move.w #1,v_state
        clr.w v_index
        ; Handles a zero-edge path as well as the supplied A-to-H examples.
        move.w v_mid,d0
        cmp.w v_target,d0
        beq.s BFSPath
        rts
.discover:
        move.w v_pending,d0
        move.w v_mid,d1
        bset d0,v_mask+1
        addq.w #1,v_swaps
        lea v_parents,a0
        move.b d1,(a0,d0.w)
        lea v_values,a0
        move.b (a0,d1.w),d2
        addq.b #1,d2
        move.b d2,(a0,d0.w)
        cmp.w v_target,d0
        beq.s BFSPath
        lea v_queue,a0
        move.w v_high,d1
        move.b d0,(a0,d1.w)
        addq.w #1,v_high
        rts
BFSPath:
        lea v_result,a0
        lea v_parents,a1
        moveq #0,d1
.back:
        move.b d0,(a0,d1.w)
        bset d0,v_result_mask+1
        addq.w #1,d1
        tst.w d0
        beq.s .reverse
        move.b (a1,d0.w),d0
        andi.w #$FF,d0
        bra.s .back
.reverse:
        move.w d1,v_result_len
        subq.w #1,d1
        moveq #0,d0
.swap:
        cmp.w d1,d0
        bhs.s .done
        move.b (a0,d0.w),d2
        move.b (a0,d1.w),(a0,d0.w)
        move.b d2,(a0,d1.w)
        addq.w #1,d0
        subq.w #1,d1
        bra.s .swap
.done:
        move.w #3,v_event
        bra.w AlgorithmComplete

; Nonpreemptive priority scheduling. All arrivals are zero. Choose by
; (priority, original burst, original ID), lower first. Each step is one tick.
ResetPriority:
        lea PriorityData(pc),a0
        move.w v_dataset,d0
        lsl.w #3,d0
        adda.w d0,a0
        move.l (a0)+,v_values
        move.l v_values,v_initial
        move.l (a0),v_aux
        clr.l v_waits
        clr.l v_waits+4
        clr.l v_turnaround
        clr.l v_turnaround+4
        rts
BeginPriority:
        clr.w v_event          ; continue running current job
        move.w v_mid,d0
        bpl.s .selected
        move.w #1,v_event      ; dispatch a new job
        moveq #-1,d0
        moveq #0,d1
        lea v_aux,a0
        lea v_initial,a1
.choose:
        btst d1,v_mask+1
        bne.s .next
        tst.w d0
        bmi.s .best
        move.b (a0,d1.w),d2
        cmp.b (a0,d0.w),d2
        blo.s .best
        bhi.s .next
        move.b (a1,d1.w),d2
        cmp.b (a1,d0.w),d2
        bhs.s .next            ; equal burst keeps earlier ID
.best:
        move.w d1,d0
.next:
        addq.w #1,d1
        cmpi.w #4,d1
        blo.s .choose
.selected:
        move.w d0,v_pending
        move.w d0,v_pair_left
        bra.w ShowStep
CommitPriority:
        move.w v_pending,d0
        tst.w v_event
        beq.s .tick
        move.w d0,v_mid
        move.w d0,d1
        add.w d1,d1
        lea v_waits,a0
        move.w v_elapsed,(a0,d1.w)
        move.w v_elapsed,d2
        add.w d2,v_total_wait
.tick:
        addq.w #1,v_elapsed
        lea v_values,a0
        subq.b #1,(a0,d0.w)
        bne.s .return
        move.w d0,d1
        add.w d1,d1
        lea v_turnaround,a0
        move.w v_elapsed,(a0,d1.w)
        lea v_result,a0
        move.w v_result_len,d1
        move.b d0,(a0,d1.w)
        addq.w #1,v_result_len
        bset d0,v_mask+1
        bset d0,v_result_mask+1
        move.w #-1,v_mid
        cmpi.w #4,v_result_len
        beq.w AlgorithmComplete
.return:
        rts

; First fit: inspect blocks from A on every request, splitting the first
; sufficiently large free block. Failure changes no capacity. No coalescing.
ResetFirstFit:
        lea FirstFitData(pc),a0
        move.w v_dataset,d0
        mulu.w #10,d0
        adda.w d0,a0
        lea v_values,a1
        moveq #4,d0
.blocks:
        move.b (a0)+,(a1)+
        dbf d0,.blocks
        lea v_aux,a1
        moveq #3,d0
.requests:
        move.b (a0)+,(a1)+
        dbf d0,.requests
        clr.w v_mid
        rts
BeginFirstFit:
        move.w v_mid,d0
        move.w d0,v_pair_left
        lea v_values,a0
        moveq #0,d1
        move.b (a0,d0.w),d1
        move.w d1,v_last_left
        lea v_aux,a0
        move.w v_low,d2
        moveq #0,d3
        move.b (a0,d2.w),d3
        move.w d3,v_last_right
        move.w #1,v_event      ; skip this undersized block
        cmp.w d3,d1
        bhs.s .fit
        cmpi.w #4,d0
        bne.s .show
        move.w #2,v_event      ; no block fits
        bra.s .show
.fit:
        clr.w v_event          ; allocate and split
.show:
        addq.w #1,v_comparisons
        bra.w ShowStep
CommitFirstFit:
        cmpi.w #1,v_event
        beq.s .next_block
        tst.w v_event
        bne.s .next_request
        move.w v_mid,d0
        lea v_values,a0
        move.w v_last_right,d1
        sub.b d1,(a0,d0.w)
        lea v_result,a0
        move.w v_low,d1
        move.b d0,(a0,d1.w)
        bset d0,v_result_mask+1
        addq.w #1,v_swaps       ; placed requests
.next_request:
        addq.w #1,v_result_len
        addq.w #1,v_low
        clr.w v_mid
        cmpi.w #4,v_low
        beq.w AlgorithmComplete
        rts
.next_block:
        addq.w #1,v_mid
        rts

SortData:
        dc.b 6,3,8,1,5,2,7,4
        dc.b 8,7,6,5,4,3,2,1
        dc.b 1,2,3,5,4,6,8,7
        dc.b 1,2,3,4,5,6,7,8
        dc.b 3,1,3,2,1,2,3,1
BinaryData:                    ; eight sorted values, target, padding
        dc.b 1,2,3,4,5,6,7,8,6,0
        dc.b 1,2,3,4,5,6,7,8,1,0
        dc.b 1,2,3,4,5,6,7,8,8,0
        dc.b 1,2,3,5,6,7,8,9,4,0
        dc.b 1,1,2,3,3,3,7,9,3,0
GraphData:                     ; eight directed adjacency bitsets, A is bit 0
        dc.b $06,$18,$20,$40,$40,$80,$80,$00 ; tree
        dc.b $02,$14,$09,$20,$20,$40,$80,$02 ; cycle
        dc.b $06,$08,$08,$01,$20,$40,$10,$00 ; H is disconnected
        dc.b $06,$08,$80,$10,$20,$40,$80,$00 ; shortcut A-C-H
        dc.b $06,$18,$18,$20,$20,$40,$80,$00 ; diamond with shared neighbors
PriorityData:                  ; bursts A-D, priorities A-D
        dc.b 4,2,5,1,2,1,3,1
        dc.b 2,3,1,4,4,3,2,1
        dc.b 5,2,4,1,1,1,1,1
        dc.b 3,3,1,1,2,2,1,1
        dc.b 9,1,2,3,1,4,3,2
FirstFitData:                  ; five free blocks, four requests, padding
        dc.b 1,5,2,3,6,2,4,1,4,0
        dc.b 2,4,1,3,5,2,4,1,3,0
        dc.b 9,2,1,1,1,2,3,4,1,0
        dc.b 1,2,1,2,1,3,4,2,9,0
        dc.b 0,5,0,2,4,1,4,2,3,0
        even
