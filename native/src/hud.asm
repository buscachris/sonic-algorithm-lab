; Six rows of the native transparent window plane. No external renderer.
; Caller masks interrupts so VBlank DMA cannot interrupt a VDP transaction.
DrawHUD:
        move.w #$8F02,VDP_CTRL
        move.w #$8334,VDP_CTRL
        move.w #$9100,VDP_CTRL
        move.w #$9206,VDP_CTRL
        tst.w v_room
        bne.w .room
        lea HubRows(pc),a0
        move.l #$50000003,d4
        moveq #5,d5
.hub_rows:
        move.l d4,VDP_CTRL
        bsr.w DrawRow
        addi.l #$00800000,d4
        dbf d5,.hub_rows
        move.w v_completed,d4
        moveq #0,d0
        moveq #AlgorithmCount-1,d5
.count:
        lsr.w #1,d4
        bcc.s .next
        addq.w #1,d0
.next:
        dbf d5,.count
        move.l #HubTitleCount,VDP_CTRL
        bra.w DrawNumber
.room:
        move.w v_algorithm,d4
        mulu.w #40,d4
        lea StageTitles(pc),a0
        adda.w d4,a0
        move.l #$50000003,VDP_CTRL
        bsr.w DrawRow
        lea StageRules(pc),a0
        adda.w d4,a0
        cmpi.w #2,v_algorithm
        blo.s .stable
        cmpi.w #7,v_algorithm
        beq.s .stable
        cmpi.w #8,v_algorithm
        bne.s .rule
.stable:
        cmpi.w #4,v_dataset
        bne.s .rule
        lea RepeatsRule(pc),a0
.rule:
        move.l #$50800003,VDP_CTRL
        bsr.w DrawRow
        move.w v_algorithm,d0
        cmpi.w #2,d0
        blo.w DrawSortHUD
        beq.w DrawBinaryHUD
        cmpi.w #3,d0
        beq.w DrawBFSHUD
        cmpi.w #4,d0
        beq.w DrawPriorityHUD
        cmpi.w #5,d0
        beq.w DrawFitHUD
        cmpi.w #8,d0
        beq.w DrawMergeHUD
        cmpi.w #11,d0
        beq.w DrawLinearHUD
        bra.w DrawSortHUD

DrawSortHUD:
        lea Counters(pc),a0
        move.l #$51000003,VDP_CTRL
        bsr.w DrawRow
        move.l #CountersCompare,VDP_CTRL
        move.w v_comparisons,d0
        bsr.w DrawNumber
        move.l #CountersSwap,VDP_CTRL
        move.w v_swaps,d0
        bsr.w DrawNumber
        move.l #CountersInput,VDP_CTRL
        bsr.w DrawInput
        lea ReadyMessage(pc),a0
        tst.w v_done
        bne.s .done
        tst.w v_phase
        bne.s .compare
        tst.w v_running
        bne.s .running
        tst.w v_comparisons
        beq.s .message
        lea PausedMessage(pc),a0
        bra.s .message
.running:
        lea RunningMessage(pc),a0
        bra.s .message
.done:
        lea DoneMessage(pc),a0
        bra.s .message
.compare:
        cmpi.w #9,v_algorithm
        beq.s .quick
        lea KeepMessage(pc),a0
        cmpi.w #6,v_algorithm
        bne.s .heap
        lea SelectionMessage(pc),a0
.heap:
        cmpi.w #10,v_algorithm
        bne.s .swap
        lea HeapMessage(pc),a0
.swap:
        tst.w v_want_swap
        beq.s .message
        lea SwapMessage(pc),a0
        bra.s .message
.quick:
        lea QuickMessage(pc),a0
        cmpi.w #2,v_event
        bne.s .message
        lea PivotMessage(pc),a0
.message:
        move.l #$51800003,VDP_CTRL
        bsr.w DrawRow
        tst.w v_phase
        beq.s .help
        move.l #$51860003,VDP_CTRL
        move.w v_last_left,d0
        bsr.w DrawDigit
        move.l #$51900003,VDP_CTRL
        move.w v_last_right,d0
        bsr.w DrawDigit
.help:
        lea SortIDs(pc),a0
        move.l #$52000003,VDP_CTRL
        bsr.w DrawRow
        cmpi.w #6,v_algorithm
        beq.w DrawSelectionIndices
        cmpi.w #7,v_algorithm
        beq.w DrawOddEvenIndices
        cmpi.w #9,v_algorithm
        beq.w DrawQuickIndices
        cmpi.w #10,v_algorithm
        beq.w DrawHeapIndices
DrawResetHelp:
        lea ResetHelp(pc),a0
        cmpi.w #6,v_algorithm
        beq.s .unstable
        cmpi.w #9,v_algorithm
        beq.s .unstable
        cmpi.w #10,v_algorithm
        bne.s .row
.unstable:
        lea UnstableIDs(pc),a0
.row:
        move.l #$52800003,VDP_CTRL
        bra.w DrawRow

DrawSelectionIndices:
        lea SelectionIndices(pc),a0
        move.l #$52000003,VDP_CTRL
        bsr.w DrawRow
        move.l #SelectionIndicesFront,VDP_CTRL
        move.w v_outer,d0
        bsr.w DrawDigit
        move.l #SelectionIndicesMin,VDP_CTRL
        move.w v_min,d0
        bsr.w DrawDigit
        move.l #SelectionIndicesScan,VDP_CTRL
        move.w v_index,d0
        bsr.w DrawDigit
        bra.w DrawResetHelp

DrawOddEvenIndices:
        lea OddEvenIndices(pc),a0
        move.l #$52000003,VDP_CTRL
        bsr.w DrawRow
        move.l #OddEvenIndicesRound,VDP_CTRL
        move.w v_pass,d0
        bsr.w DrawDigit
        move.l #OddEvenIndicesStart,VDP_CTRL
        move.w v_state,d0
        bsr.w DrawDigit
        bra.w DrawResetHelp

DrawQuickIndices:
        lea QuickIndices(pc),a0
        move.l #$52000003,VDP_CTRL
        bsr.w DrawRow
        move.l #QuickIndicesLow,VDP_CTRL
        move.w v_low,d0
        bsr.w DrawDigit
        move.l #QuickIndicesHigh,VDP_CTRL
        move.w v_high,d0
        bsr.w DrawDigit
        move.l #QuickIndicesSlot,VDP_CTRL
        move.w v_outer,d0
        bsr.w DrawDigit
        move.l #QuickIndicesStack,VDP_CTRL
        move.w v_stack_len,d0
        bsr.w DrawDigit
        bra.w DrawResetHelp

DrawHeapIndices:
        lea HeapIndices(pc),a0
        move.l #$52000003,VDP_CTRL
        bsr.w DrawRow
        move.l #HeapIndicesSize,VDP_CTRL
        move.w v_heap_size,d0
        bsr.w DrawDigit
        move.l #HeapIndicesRoot,VDP_CTRL
        move.w v_root,d0
        bsr.w DrawDigit
        move.l #HeapIndicesSorted,VDP_CTRL
        moveq #8,d0
        sub.w v_heap_size,d0
        tst.w v_done
        beq.s .count
        moveq #8,d0
.count:
        bsr.w DrawDigit
        bra.w DrawResetHelp

DrawMergeHUD:
        lea MergeCounters(pc),a0
        move.l #$51000003,VDP_CTRL
        bsr.w DrawRow
        move.l #MergeCountersCompare,VDP_CTRL
        move.w v_comparisons,d0
        bsr.w DrawNumber
        move.l #MergeCountersWrites,VDP_CTRL
        move.w v_swaps,d0
        bsr.w DrawNumber
        move.l #MergeCountersInput,VDP_CTRL
        bsr.w DrawInput
        lea MergeStep(pc),a0
        tst.w v_done
        beq.s .step
        lea DoneMessage(pc),a0
.step:
        move.l #$51800003,VDP_CTRL
        bsr.w DrawRow
        tst.w v_done
        bne.s .buffer
        move.l #MergeStepWidth,VDP_CTRL
        move.w v_width,d0
        bsr.w DrawDigit
        move.l #MergeStepSource,VDP_CTRL
        move.w v_pending,d0
        tst.w v_phase
        bne.s .source
        moveq #-1,d0
.source:
        bsr.w DrawDigit
        move.l #MergeStepWrite,VDP_CTRL
        move.w v_write,d0
        bsr.w DrawDigit
.buffer:
        lea MergeBuffer(pc),a0
        move.l #$52000003,VDP_CTRL
        bsr.w DrawRow
        move.l #MergeBufferValues,VDP_CTRL
        lea v_aux,a0
        moveq #0,d4
.values:
        moveq #0,d0
        move.b (a0,d4.w),d0
        bsr.w DrawDigit
        addq.w #1,d4
        cmpi.w #8,d4
        blo.s .values
        move.l #MergeBufferIDs,VDP_CTRL
        lea v_initial,a0
        moveq #0,d4
.ids:
        moveq #0,d0
        move.b (a0,d4.w),d0
        bsr.w DrawID
        addq.w #1,d4
        cmpi.w #8,d4
        blo.s .ids
        bra.w DrawResetHelp

DrawLinearHUD:
        lea BinaryCounters(pc),a0
        move.l #$51000003,VDP_CTRL
        bsr.w DrawRow
        move.l #BinaryCountersTarget,VDP_CTRL
        move.w v_target,d0
        bsr.w DrawDigit
        move.l #BinaryCountersTests,VDP_CTRL
        move.w v_comparisons,d0
        bsr.w DrawNumber
        move.l #BinaryCountersInput,VDP_CTRL
        bsr.w DrawInput
        lea LinearCursor(pc),a0
        move.l #$51800003,VDP_CTRL
        bsr.w DrawRow
        move.l #LinearCursorIndex,VDP_CTRL
        move.w v_mid,d0
        bsr.w DrawDigit
        move.l #LinearCursorValue,VDP_CTRL
        move.w v_last_left,d0
        tst.w v_operations
        bne.s .value
        moveq #-1,d0
.value:
        bsr.w DrawDigit
        move.l #LinearCursorTarget,VDP_CTRL
        move.w v_target,d0
        bsr.w DrawDigit
        lea LinearResult(pc),a0
        move.l #$52000003,VDP_CTRL
        bsr.w DrawRow
        move.l #LinearResultFound,VDP_CTRL
        moveq #-1,d0
        tst.w v_result_len
        beq.s .found
        moveq #0,d0
        move.b v_result,d0
.found:
        bsr.w DrawDigit
        lea LinearReady(pc),a0
        tst.w v_operations
        beq.s .message
        lea LinearNext(pc),a0
        tst.w v_done
        beq.s .message
        lea BinaryEqual(pc),a0
        tst.w v_result_len
        bne.s .message
        lea BinaryAbsent(pc),a0
.message:
        move.l #$52800003,VDP_CTRL
        bra.w DrawRow

DrawBinaryHUD:
        lea BinaryCounters(pc),a0
        move.l #$51000003,VDP_CTRL
        bsr.w DrawRow
        move.l #BinaryCountersTarget,VDP_CTRL
        move.w v_target,d0
        bsr.w DrawDigit
        move.l #BinaryCountersTests,VDP_CTRL
        move.w v_comparisons,d0
        bsr.w DrawNumber
        move.l #BinaryCountersInput,VDP_CTRL
        bsr.w DrawInput
        lea BinaryBounds(pc),a0
        move.l #$51800003,VDP_CTRL
        bsr.w DrawRow
        move.l #BinaryBoundsLow,VDP_CTRL
        move.w v_low,d0
        bsr.w DrawID
        move.l #BinaryBoundsHigh,VDP_CTRL
        move.w v_high,d0
        bsr.w DrawID
        move.l #BinaryBoundsMid,VDP_CTRL
        move.w v_mid,d0
        bsr.w DrawID
        moveq #-1,d0
        move.w v_mid,d1
        cmpi.w #8,d1
        bhs.s .value
        lea v_values,a0
        moveq #0,d0
        move.b (a0,d1.w),d0
.value:
        move.l #BinaryBoundsValue,VDP_CTRL
        bsr.w DrawDigit
        lea BinaryCandidates(pc),a0
        move.l #$52000003,VDP_CTRL
        bsr.w DrawRow
        move.l #BinaryCandidatesList,VDP_CTRL
        moveq #0,d4
.candidates:
        moveq #0,d0
        tst.w v_done
        bne.s .finished
        cmp.w v_low,d4
        blt.s .candidate
        cmp.w v_high,d4
        bgt.s .candidate
        bra.s .letter
.finished:
        btst d4,v_result_mask+1
        beq.s .candidate
.letter:
        move.w d4,d0
        addi.w #LetterA,d0
.candidate:
        bsr.w DrawGlyph
        addq.w #1,d4
        cmpi.w #8,d4
        blo.s .candidates
        move.l #BinaryCandidatesFound,VDP_CTRL
        moveq #-1,d0
        tst.w v_result_len
        beq.s .found
        moveq #0,d0
        move.b v_result,d0
.found:
        bsr.w DrawID
        lea ResetHelp(pc),a0
        tst.w v_operations
        beq.s .explain
        lea BinaryAbsent(pc),a0
        tst.w v_done
        beq.s .event
        tst.w v_result_len
        beq.s .explain
.event:
        lea BinaryLess(pc),a0
        tst.w v_event
        beq.s .explain
        lea BinaryEqual(pc),a0
        cmpi.w #1,v_event
        beq.s .explain
        lea BinaryGreater(pc),a0
.explain:
        move.l #$52800003,VDP_CTRL
        bra.w DrawRow

DrawBFSHUD:
        lea BFSCounters(pc),a0
        move.l #$51000003,VDP_CTRL
        bsr.w DrawRow
        move.l #BFSCountersSeen,VDP_CTRL
        move.w v_swaps,d0
        bsr.w DrawDigit
        move.l #BFSCountersInput,VDP_CTRL
        bsr.w DrawInput
        move.l #BFSCountersQueue,VDP_CTRL
        lea v_queue,a0
        move.w v_low,d4
.queue:
        cmp.w v_high,d4
        bhs.s .status
        moveq #0,d0
        move.b (a0,d4.w),d0
        bsr.w DrawID
        addq.w #1,d4
        bra.s .queue
.status:
        tst.w v_done
        bne.w .done
        lea BFSReady(pc),a0
        tst.w v_operations
        beq.s .message
        lea BFSDequeue(pc),a0
        tst.w v_event
        beq.s .message
        lea BFSSeen(pc),a0
        cmpi.w #1,v_event
        beq.s .message
        lea BFSDiscover(pc),a0
.message:
        move.l #$51800003,VDP_CTRL
        bsr.w DrawRow
        tst.w v_operations
        beq.w .graph
        tst.w v_event
        bne.s .edge
        move.l #$51920003,VDP_CTRL ; DEQUEUE at column 9
        move.w v_pending,d0
        bsr.w DrawID
        bra.w .graph
.edge:
        move.l #$518C0003,VDP_CTRL ; source at column 6
        move.w v_mid,d0
        bsr.w DrawID
        move.l #$51940003,VDP_CTRL ; destination at column 10
        move.w v_pending,d0
        bsr.w DrawID
        bra.s .graph
.done:
        lea BFSAbsent(pc),a0
        tst.w v_result_len
        beq.s .absent
        lea BFSPathRow(pc),a0
        move.l #$51800003,VDP_CTRL
        bsr.w DrawRow
        move.l #BFSPathRowDistance,VDP_CTRL
        move.w v_result_len,d0
        subq.w #1,d0
        bsr.w DrawDigit
        move.l #BFSPathRowPath,VDP_CTRL
        lea v_result,a0
        moveq #0,d4
.path:
        moveq #0,d0
        move.b (a0,d4.w),d0
        bsr.w DrawID
        addq.w #1,d4
        cmp.w v_result_len,d4
        bhs.s .graph
        moveq #GlyphGreater,d0
        bsr.w DrawGlyph
        bra.s .path
.absent:
        move.l #$51800003,VDP_CTRL
        bsr.w DrawRow
.graph:
        lea BlankRow(pc),a0
        move.l #$52000003,VDP_CTRL
        bsr.w DrawRow
        lea BlankRow(pc),a0
        move.l #$52800003,VDP_CTRL
        bsr.w DrawRow
        moveq #0,d5
        lea v_graph,a0
        move.l #$52020003,VDP_CTRL
.vertex:
        cmpi.w #4,d5
        bne.s .prefix
        move.l #$52820003,VDP_CTRL
.prefix:
        move.w d5,d0
        bsr.w DrawID
        moveq #GlyphGreater,d0
        bsr.w DrawGlyph
        moveq #0,d6
        move.b (a0,d5.w),d6
        moveq #6,d7           ; seven remaining columns per vertex
        moveq #0,d2
        tst.b d6
        bne.s .neighbors
        moveq #GlyphDash,d0
        bsr.w DrawGlyph
        subq.w #1,d7
        bra.s .padding
.neighbors:
        btst d2,d6
        beq.s .next_neighbor
        move.w d2,d0
        bsr.w DrawID
        subq.w #1,d7
.next_neighbor:
        addq.w #1,d2
        cmpi.w #8,d2
        blo.s .neighbors
.padding:
        moveq #0,d0
        bsr.w DrawGlyph
        dbf d7,.padding
        addq.w #1,d5
        cmpi.w #8,d5
        blo.s .vertex
        rts

DrawPriorityHUD:
        lea PriorityCounters(pc),a0
        move.l #$51000003,VDP_CTRL
        bsr.w DrawRow
        move.l #PriorityCountersTime,VDP_CTRL
        move.w v_elapsed,d0
        bsr.w DrawNumber
        move.l #PriorityCountersWait,VDP_CTRL
        move.w v_total_wait,d0
        bsr.w DrawNumber
        move.l #PriorityCountersInput,VDP_CTRL
        bsr.w DrawInput
        lea PriorityReady(pc),a0
        tst.w v_operations
        beq.s .message
        lea PriorityDone(pc),a0
        tst.w v_done
        bne.s .message
        lea PriorityTick(pc),a0
.message:
        move.l #$51800003,VDP_CTRL
        bsr.w DrawRow
        tst.w v_operations
        beq.s .order
        tst.w v_done
        bne.s .order
        move.w v_mid,d4
        bpl.s .job
        move.w v_pending,d4
.job:
        move.l #PriorityTickJob,VDP_CTRL
        move.w d4,d0
        bsr.w DrawID
        lea v_values,a0
        moveq #0,d0
        move.b (a0,d4.w),d0
        move.l #PriorityTickBurst,VDP_CTRL
        bsr.w DrawDigit
.order:
        lea PriorityOrder(pc),a0
        move.l #$52000003,VDP_CTRL
        bsr.w DrawRow
        move.l #PriorityOrderPriorities,VDP_CTRL
        lea v_aux,a0
        moveq #0,d4
.priorities:
        move.w d4,d0
        bsr.w DrawID
        moveq #0,d0
        move.b (a0,d4.w),d0
        bsr.w DrawDigit
        moveq #0,d0
        bsr.w DrawGlyph
        addq.w #1,d4
        cmpi.w #4,d4
        blo.s .priorities
        move.l #PriorityOrderOrder,VDP_CTRL
        lea v_result,a0
        moveq #0,d4
.completed:
        cmp.w v_result_len,d4
        bhs.s .waits
        moveq #0,d0
        move.b (a0,d4.w),d0
        bsr.w DrawID
        addq.w #1,d4
        bra.s .completed
.waits:
        lea PriorityWaits(pc),a0
        move.l #$52800003,VDP_CTRL
        bsr.w DrawRow
        move.l #PriorityWaitsA,VDP_CTRL
        move.w v_waits,d0
        bsr.w DrawNumber
        move.l #PriorityWaitsB,VDP_CTRL
        move.w v_waits+2,d0
        bsr.w DrawNumber
        move.l #PriorityWaitsC,VDP_CTRL
        move.w v_waits+4,d0
        bsr.w DrawNumber
        move.l #PriorityWaitsD,VDP_CTRL
        move.w v_waits+6,d0
        bra.w DrawNumber

DrawFitHUD:
        lea FitCounters(pc),a0
        move.l #$51000003,VDP_CTRL
        bsr.w DrawRow
        move.l #FitCountersChecks,VDP_CTRL
        move.w v_comparisons,d0
        bsr.w DrawNumber
        move.l #FitCountersPlaced,VDP_CTRL
        move.w v_swaps,d0
        bsr.w DrawDigit
        move.l #FitCountersInput,VDP_CTRL
        bsr.w DrawInput
        lea FitScan(pc),a0
        tst.w v_done
        beq.s .scan
        lea FirstFitDone(pc),a0
        move.l #$51800003,VDP_CTRL
        bsr.w DrawRow
        bra.s .requests
.scan:
        move.l #$51800003,VDP_CTRL
        bsr.w DrawRow
        move.l #FitScanRequest,VDP_CTRL
        move.w v_low,d0
        addq.w #1,d0
        bsr.w DrawDigit
        lea v_aux,a0
        move.w v_low,d1
        moveq #0,d0
        move.b (a0,d1.w),d0
        move.l #FitScanNeed,VDP_CTRL
        bsr.w DrawDigit
        move.l #FitScanBlock,VDP_CTRL
        move.w v_mid,d0
        bsr.w DrawID
        lea v_values,a0
        move.w v_mid,d1
        moveq #0,d0
        move.b (a0,d1.w),d0
        move.l #FitScanFree,VDP_CTRL
        bsr.w DrawDigit
.requests:
        lea FitRequests(pc),a0
        move.l #$52000003,VDP_CTRL
        bsr.w DrawRow
        move.l #FitRequestsRequests,VDP_CTRL
        lea v_aux,a0
        moveq #0,d4
.request:
        move.w d4,d0
        addq.w #1,d0
        bsr.w DrawDigit
        moveq #GlyphEquals,d0
        bsr.w DrawGlyph
        moveq #0,d0
        move.b (a0,d4.w),d0
        bsr.w DrawDigit
        moveq #0,d0
        bsr.w DrawGlyph
        addq.w #1,d4
        cmpi.w #4,d4
        blo.s .request
        lea FitResults(pc),a0
        move.l #$52800003,VDP_CTRL
        bsr.w DrawRow
        move.l #FitResultsResults,VDP_CTRL
        lea v_result,a0
        moveq #0,d4
.result:
        move.w d4,d0
        addq.w #1,d0
        bsr.w DrawDigit
        moveq #GlyphEquals,d0
        bsr.w DrawGlyph
        cmp.w v_result_len,d4
        blo.s .assigned
        moveq #GlyphQuestion,d0
        bsr.w DrawGlyph
        bra.s .next
.assigned:
        moveq #0,d0
        move.b (a0,d4.w),d0
        bsr.w DrawID
.next:
        moveq #0,d0
        bsr.w DrawGlyph
        addq.w #1,d4
        cmpi.w #4,d4
        blo.s .result
        rts

DrawInput:
        lea InputNames(pc),a0
        move.w v_algorithm,d0
        mulu.w #40,d0
        adda.w d0,a0
        move.w v_dataset,d0
        lsl.w #3,d0
        adda.w d0,a0
        moveq #7,d1
        bra.s DrawText
DrawRow:
        moveq #39,d1
DrawText:
        moveq #0,d0
.loop:
        move.b (a0)+,d0
        addi.w #$8000+LabTile,d0
        move.w d0,VDP_DATA
        moveq #0,d0
        dbf d1,.loop
        rts
DrawID:
        cmpi.w #8,d0
        bhs.s DrawDash
        addi.w #LetterA,d0
        bra.s DrawGlyph
DrawDigit:
        cmpi.w #10,d0
        bhs.s DrawDash
        addi.w #DigitZero,d0
        bra.s DrawGlyph
DrawDash:
        moveq #GlyphDash,d0
DrawGlyph:
        addi.w #$8000+LabTile,d0
        move.w d0,VDP_DATA
        rts
DrawNumber:
        andi.l #$FFFF,d0
        divu.w #10,d0
        move.w d0,d1
        addi.w #$8000+LabTile+DigitZero,d1
        move.w d1,VDP_DATA
        swap d0
        addi.w #$8000+LabTile+DigitZero,d0
        move.w d0,VDP_DATA
        rts
