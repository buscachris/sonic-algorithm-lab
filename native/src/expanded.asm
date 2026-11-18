; Additional demonstrations. Each visible operation is computed from current
; RAM, shown for 36 frames, then committed by the shared animation engine.
ResetExpanded:
        cmpi.w #11,d0
        beq.w ResetLinear
        bsr.w CopySortInput
        move.w #1,v_pass
        move.w v_algorithm,d0
        cmpi.w #6,d0
        beq.s .selection
        cmpi.w #7,d0
        beq.s .return
        cmpi.w #8,d0
        beq.s .merge
        cmpi.w #9,d0
        beq.s .quick
        move.w #8,v_heap_size
        move.w #3,v_outer
        move.w #3,v_root
        move.w #3,v_min
        move.w #1,v_build
        rts
.selection:
        move.w #1,v_index
.return:
        rts
.merge:
        move.l #-1,v_aux
        move.l #-1,v_aux+4
        move.l #-1,v_initial
        move.l #-1,v_initial+4
        move.w #1,v_width
        bra.w MergeSetup
.quick:
        move.w #7,v_high
        clr.w v_pass
        bra.w QuickRange

BeginExpanded:
        cmpi.w #6,d0
        beq.w BeginSelection
        cmpi.w #7,d0
        beq.w BeginOddEven
        cmpi.w #8,d0
        beq.w BeginMerge
        cmpi.w #9,d0
        beq.w BeginQuick
        cmpi.w #10,d0
        beq.w BeginHeap
        bra.w BeginLinear

AdvanceExpanded:
        move.w v_algorithm,d0
        cmpi.w #6,d0
        beq.w AdvanceSelection
        cmpi.w #7,d0
        beq.w AdvanceOddEven
        cmpi.w #9,d0
        beq.w AdvanceQuick
        bra.w AdvanceHeap

ReadPair:
        lea v_values,a0
        move.w v_pair_left,d2
        move.w v_pair_right,d3
        moveq #0,d0
        moveq #0,d1
        move.b (a0,d2.w),d0
        move.b (a0,d3.w),d1
        move.w d0,v_last_left
        move.w d1,v_last_right
        rts

ShowSortStep:
        addq.w #1,v_operations
        move.w #3,v_message
        tst.w v_want_swap
        beq.s .show
        move.w #2,v_message
.show:
        move.w #2,v_phase
        bra.w ShowOperation

; Selection: find the minimum of each suffix, then exchange it with the
; suffix's first item. Equal minima keep the first candidate; not stable.
BeginSelection:
        clr.w v_want_swap
        clr.w v_event
        move.w v_min,v_pair_left
        move.w v_index,v_pair_right
        tst.w v_state
        beq.s .scan
        move.w v_outer,v_pair_left
        move.w v_min,v_pair_right
        move.w #1,v_want_swap
        move.w #1,v_event
        bsr.w ReadPair
        bra.w ShowSortStep
.scan:
        bsr.w ReadPair
        addq.w #1,v_comparisons
        bra.w ShowSortStep

AdvanceSelection:
        tst.w v_event
        bne.s .next
        move.w v_last_right,d0
        cmp.w v_last_left,d0
        bhs.s .scan_next
        move.w v_index,v_min
.scan_next:
        addq.w #1,v_index
        cmpi.w #8,v_index
        blo.s .return
        move.w v_min,d0
        cmp.w v_outer,d0
        beq.s .next
        move.w #1,v_state
        rts
.next:
        addq.w #1,v_outer
        cmpi.w #7,v_outer
        beq.w AlgorithmComplete
        move.w v_outer,v_min
        move.w v_outer,v_index
        addq.w #1,v_index
        addq.w #1,v_pass
        clr.w v_state
.return:
        rts

; Odd-even transposition: compare even-index pairs, then odd-index pairs.
; Stop only after an entire two-parity round made no exchanges. Stable.
BeginOddEven:
        move.w v_index,d0
        move.w d0,v_pair_left
        addq.w #1,d0
        move.w d0,v_pair_right
        bra.w CompareNow

AdvanceOddEven:
        tst.w v_want_swap
        beq.s .next
        move.w #1,v_pass_swapped
.next:
        addq.w #2,v_index
        cmpi.w #7,v_index
        blo.s .return
        tst.w v_state
        bne.s .round_done
        move.w #1,v_state
        move.w #1,v_index
        rts
.round_done:
        tst.w v_pass_swapped
        beq.w AlgorithmComplete
        clr.w v_state
        clr.w v_index
        clr.w v_pass_swapped
        addq.w #1,v_pass
.return:
        rts

; Stable bottom-up merge. Each step copies one chosen input to a buffer.
; Publish a complete merged segment atomically so the main row always
; contains exactly the original eight value/ID pairs.
MergeSetup:
        move.w v_base,d0
        move.w d0,v_low
        move.w d0,v_write
        add.w v_width,d0
        move.w d0,v_mid
        move.w d0,v_high
        add.w v_width,d0
        move.w d0,v_end
        rts

BeginMerge:
        move.w #-1,v_last_left
        move.w #-1,v_last_right
        lea v_values,a0
        move.w v_low,d0
        cmp.w v_mid,d0
        bhs.s .right_only
        move.w d0,v_pair_left
        moveq #0,d2
        move.b (a0,d0.w),d2
        move.w d2,v_last_left
        move.w v_high,d1
        cmp.w v_end,d1
        bhs.s .left_only
        move.w d1,v_pair_right
        moveq #0,d3
        move.b (a0,d1.w),d3
        move.w d3,v_last_right
        addq.w #1,v_comparisons
        clr.w v_event
        cmp.w d3,d2
        bls.s .choose_left
        move.w #1,v_event
        bra.s .choose_right
.left_only:
        move.w #2,v_event
.choose_left:
        move.w d0,v_pending
        bra.w ShowStep
.right_only:
        move.w v_high,d1
        move.w d1,v_pair_right
        moveq #0,d3
        move.b (a0,d1.w),d3
        move.w d3,v_last_right
        move.w #3,v_event
.choose_right:
        move.w d1,v_pending
        bra.w ShowStep

CommitMerge:
        move.w v_pending,d0
        move.w v_write,d1
        lea v_values,a0
        lea v_aux,a1
        move.b (a0,d0.w),(a1,d1.w)
        lea v_ids,a0
        lea v_initial,a1
        move.b (a0,d0.w),(a1,d1.w)
        btst #0,v_event+1
        bne.s .right
        addq.w #1,v_low
        bra.s .written
.right:
        addq.w #1,v_high
.written:
        addq.w #1,v_write
        addq.w #1,v_swaps       ; buffer writes, shown as WRITE in this room
        move.w v_write,d0
        cmp.w v_end,d0
        blo.s .return
        move.w v_base,d0
        lea v_values,a0
        lea v_aux,a1
        lea v_ids,a2
        lea v_initial,a3
.publish:
        move.b (a1,d0.w),(a0,d0.w)
        move.b (a3,d0.w),(a2,d0.w)
        addq.w #1,d0
        cmp.w v_end,d0
        blo.s .publish
        move.w v_end,v_base
        cmpi.w #8,v_base
        blo.w MergeSetup
        addq.w #1,v_pass
        move.w v_width,d0
        add.w d0,d0
        move.w d0,v_width
        cmpi.w #8,d0
        beq.w AlgorithmComplete
        clr.w v_base
        bra.w MergeSetup
.return:
        rts

; Iterative Lomuto quicksort, last element pivot, <= partition comparison.
; Pending ranges use an explicit eight-entry stack. Self-swaps are skipped.
QuickRange:
        clr.w v_state
        move.w v_low,v_outer
        move.w v_low,v_index
        lea v_values,a0
        move.w v_high,d0
        clr.w v_pivot
        move.b (a0,d0.w),v_pivot+1
        addq.w #1,v_pass
        rts

BeginQuick:
        clr.w v_want_swap
        tst.w v_state
        bne.s .pivot
        move.w v_index,v_pair_left
        move.w v_high,v_pair_right
        bsr.w ReadPair
        addq.w #1,v_comparisons
        clr.w v_event
        cmp.w v_pivot,d0
        bhi.s .show
        move.w #1,v_event
        move.w v_outer,d0
        cmp.w v_index,d0
        beq.s .show
        move.w d0,v_pair_left
        move.w v_index,v_pair_right
        move.w #1,v_want_swap
        bra.s .show
.pivot:
        move.w #2,v_event
        move.w v_outer,v_pair_left
        move.w v_high,v_pair_right
        bsr.w ReadPair
        move.w v_outer,d0
        cmp.w v_high,d0
        beq.s .show
        move.w #1,v_want_swap
.show:
        bra.w ShowSortStep

AdvanceQuick:
        tst.w v_state
        bne.s .partition_done
        tst.w v_event
        beq.s .next
        addq.w #1,v_outer
.next:
        addq.w #1,v_index
        move.w v_index,d0
        cmp.w v_high,d0
        blo.s .return
        move.w #1,v_state
.return:
        rts
.partition_done:
        move.w v_low,d0
        move.w v_outer,d1
        subq.w #1,d1
        bsr.s QuickPush
        move.w v_outer,d0
        addq.w #1,d0
        move.w v_high,d1
        bsr.s QuickPush
        tst.w v_stack_len
        beq.w AlgorithmComplete
        subq.w #1,v_stack_len
        move.w v_stack_len,d0
        lsl.w #2,d0
        lea v_stack,a0
        move.w (a0,d0.w),v_low
        move.w 2(a0,d0.w),v_high
        bra.w QuickRange

QuickPush:
        cmp.w d1,d0
        bge.s .return
        move.w v_stack_len,d2
        lsl.w #2,d2
        lea v_stack,a0
        move.w d0,(a0,d2.w)
        move.w d1,2(a0,d2.w)
        addq.w #1,v_stack_len
.return:
        rts

; Heap sort: bottom-up max-heap construction, then root/end exchanges.
; Child comparisons, sift exchanges and extractions are distinct steps.
BeginHeap:
        clr.w v_want_swap
        move.w v_state,v_event
        cmpi.w #2,v_state
        beq.s .sift_swap
        cmpi.w #3,v_state
        beq.s .extract
        move.w v_root,d0
        add.w d0,d0
        addq.w #1,d0
        tst.w v_state
        beq.s .child
        addq.w #1,d0
.child:
        move.w d0,v_child
        move.w d0,v_pair_right
        move.w v_min,v_pair_left
        bsr.w ReadPair
        addq.w #1,v_comparisons
        bra.w ShowSortStep
.sift_swap:
        move.w v_root,v_pair_left
        move.w v_min,v_pair_right
        bra.s .exchange
.extract:
        clr.w v_pair_left
        move.w v_heap_size,d0
        subq.w #1,d0
        move.w d0,v_pair_right
.exchange:
        move.w #1,v_want_swap
        bsr.w ReadPair
        bra.w ShowSortStep

AdvanceHeap:
        cmpi.w #2,v_event
        beq.s .sifted
        cmpi.w #3,v_event
        beq.s .extracted
        move.w v_last_right,d0
        cmp.w v_last_left,d0
        bls.s .compared
        move.w v_child,v_min
.compared:
        tst.w v_event
        bne.s .choose
        move.w v_child,d0
        addq.w #1,d0
        cmp.w v_heap_size,d0
        bhs.s .choose
        move.w #1,v_state
        rts
.choose:
        move.w v_root,d0
        cmp.w v_min,d0
        beq.w HeapSiftDone
        move.w #2,v_state
        rts
.sifted:
        move.w v_min,v_root
        bra.s .children
.extracted:
        subq.w #1,v_heap_size
        cmpi.w #1,v_heap_size
        beq.w AlgorithmComplete
        clr.w v_root
        clr.w v_min
        addq.w #1,v_pass
.children:
        move.w v_root,d0
        add.w d0,d0
        addq.w #1,d0
        cmp.w v_heap_size,d0
        bhs.w HeapSiftDone
        clr.w v_state
        rts

HeapSiftDone:
        tst.w v_build
        beq.s .extract
        subq.w #1,v_outer
        bmi.s .built
        move.w v_outer,v_root
        move.w v_outer,v_min
        clr.w v_state
        rts
.built:
        clr.w v_build
.extract:
        move.w #3,v_state
        rts

; Linear search: inspect unsorted positions from A to H; stop at first match.
ResetLinear:
        lea LinearData(pc),a0
        move.w v_dataset,d0
        mulu.w #10,d0
        adda.w d0,a0
        bsr.w CopyEightValues
        moveq #0,d0
        move.b (a0),d0
        move.w d0,v_target
        rts

BeginLinear:
        move.w v_index,d0
        move.w d0,v_mid
        move.w d0,v_pair_left
        lea v_values,a0
        moveq #0,d1
        move.b (a0,d0.w),d1
        move.w d1,v_last_left
        move.w v_target,v_last_right
        clr.w v_event
        cmp.w v_target,d1
        bne.s .show
        move.w #1,v_event
.show:
        addq.w #1,v_comparisons
        bra.w ShowStep

CommitLinear:
        tst.w v_event
        beq.s .next
        move.w v_mid,d0
        move.b d0,v_result
        move.w #1,v_result_len
        bset d0,v_result_mask+1
        bra.w AlgorithmComplete
.next:
        addq.w #1,v_index
        cmpi.w #8,v_index
        beq.w AlgorithmComplete
        rts

LinearData:
        dc.b 6,3,8,1,5,2,7,4,5,0
        dc.b 6,3,8,1,5,2,7,4,6,0
        dc.b 6,3,8,1,5,2,7,4,4,0
        dc.b 6,3,8,1,5,2,7,4,9,0
        dc.b 3,1,3,2,1,2,3,1,1,0
        even
