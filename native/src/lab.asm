        include "native/src/ram.inc"
        org $120000
; Export directory consumed by the patch builder, not executable vectors.
        dc.b "SAL2"
        dc.l LabBoot,LabInitHook,LabFrameHook,ObjLabSwitch,ObjLabRing,ObjLabMonitor
        dc.l LabEnd,ResetWorld,BeginStep,LabLoadHook
        dc.l LabLayout,GHZChunks,MZChunks,TileArt,LZChunks,SLZChunks,SYZChunks,SBZChunks

LabBoot:
        move.b #1,$FFFFB060
        move.l #$53414C32,v_magic
        move.w #$0600,v_version
        move.w #$0001,Zone
        move.w #$FFFF,$FFFFB02C
        move.b #3,$FFFFFE12
        move.b #$0C,$FFFFF600
        jmp $3A0

; Completing a native act returns to the hub instead of entering an act that
; has no lab stations. Death/retry in any example still reloads that room.
LabLoadHook:
        moveq #AlgorithmCount,d0
        lea Routes(pc),a0
.match:
        move.w (a0)+,d1
        cmp.w Zone,d1
        beq.s .load
        dbf d0,.match
        move.w #$0001,Zone
        clr.b $FFFFFE30
        clr.b $FFFFB03A
        move.w #$FFFF,$FFFFB02C
.load:
        jsr $1484
        move.l #0,$FFFFB280
        jmp $4E22

LabInitHook:
        movem.l d0-d7/a0-a6,-(sp)
        bsr.w LabInit
        movem.l (sp)+,d0-d7/a0-a6
        jmp ExecuteObjects

LabInit:
        clr.w v_age
        clr.w v_route
        clr.w v_gates
        clr.w $FFFFB330       ; this lab owns the native window plane
        clr.b $FFFFD040       ; replace the score HUD with lab explanations
        clr.b $FFFFD080       ; title-card art is now reusable
        clr.b $FFFFD0C0
        clr.b $FFFFD100
        clr.b $FFFFD140
        lea $FFFFD400,a0      ; 24 reserved slots for the twelve hub stations
        moveq #0,d0
        move.w #$17F,d1
.clear_slots:
        move.l d0,(a0)+
        dbf d1,.clear_slots
        clr.w v_room
        move.w #960,v_floor
        move.w #856,v_row_y
        cmpi.w #$0001,Zone
        beq.s .hub
        moveq #0,d0
        lea Routes(pc),a0
.match:
        move.w (a0)+,d1
        cmp.w Zone,d1
        beq.s .matched
        addq.w #1,d0
        bra.s .match
.matched:
        move.w d0,v_algorithm
        addq.w #1,d0
        move.w d0,v_room
        tst.b Zone
        beq.s .room
        move.w #640,v_floor
        move.w #536,v_row_y
.room:
        bsr.w ResetWorld
        bsr.w SpawnRoom
        bra.s .art
.hub:
        clr.w v_running
        clr.w v_phase
        bsr.w SpawnHub
.art:
        move.w sr,-(sp)
        move.w #$2700,sr
        move.w #$8F02,VDP_CTRL
        move.l #$70000002,VDP_CTRL ; VRAM B000: former title-card tiles
        lea TileArt,a0
        move.w #(TileArtEnd-TileArt)/2-1,d0
.tiles:
        move.w (a0)+,VDP_DATA
        dbf d0,.tiles
        ; Decode the actual native MZ pressure switch into our reserved tiles.
        move.l #((($B000+SwitchTile*32)&$3FFF)<<16)+$40000000+(($B000+SwitchTile*32)>>14),VDP_CTRL
        lea $4A02C,a0
        jsr $256E
        ; The six-row window occupies D000-D2FF. Keep a native monitor body
        ; in our reserved art, copied before the HUD touches its original PLC.
        ; The level loader has finished all queued PLCs before this hook.
        move.l #$12000003,d1 ; read VRAM D200
        move.l #((($B000+MonitorTile*32)&$3FFF)<<16)+$40000000+(($B000+MonitorTile*32)>>14),d2
        move.w #255,d3
.monitor_body:
        move.l d1,VDP_CTRL
        move.w VDP_DATA,d0
        move.l d2,VDP_CTRL
        move.w d0,VDP_DATA
        addi.l #$00020000,d1
        addi.l #$00020000,d2
        dbf d3,.monitor_body
        move.w #$8334,VDP_CTRL ; window at D000
        move.w #$9100,VDP_CTRL
        move.w #$9206,VDP_CTRL ; top six character rows
        bsr.w DrawHUD
        ; Direct boot skips the original menu, which normally enables display.
        ori.w #$40,$FFFFF60C
        move.w $FFFFF60C,VDP_CTRL
        move.w (sp)+,sr
        rts

; Spawn records: id, action/subtype, world X, world Y, then FF sentinel.
SpawnHub:
        lea HubObjects(pc),a1
        lea $FFFFD400,a0
        bra.s SpawnList
SpawnRoom:
        lea RoomObjects(pc),a1
        lea $FFFFD400,a0
SpawnList:
        move.b (a1)+,d0
        cmpi.b #$FF,d0
        beq.s .end
        move.b d0,(a0)
        move.b (a1)+,$28(a0)
        move.w (a1)+,8(a0)
        move.w (a1)+,d0
        add.w v_floor,d0
        move.w d0,$C(a0)
        lea $40(a0),a0
        bra.s SpawnList
.end:
        rts
HubObjects:
        dc.b $E0,0
        dc.w 96,-5
        dc.b $E0,1
        dc.w 208,-5
        dc.b $E0,2
        dc.w 320,-5
        dc.b $E0,3
        dc.w 432,-5
        dc.b $E0,4
        dc.w 544,-5
        dc.b $E0,5
        dc.w 656,-5
        dc.b $E0,6
        dc.w 768,-5
        dc.b $E0,7
        dc.w 880,-5
        dc.b $E0,8
        dc.w 992,-5
        dc.b $E0,9
        dc.w 1104,-5
        dc.b $E0,10
        dc.w 1216,-5
        dc.b $E0,11
        dc.w 1328,-5
        dc.b $E1,0
        dc.w 96,-84
        dc.b $E1,1
        dc.w 208,-84
        dc.b $E1,2
        dc.w 320,-84
        dc.b $E1,3
        dc.w 432,-84
        dc.b $E1,4
        dc.w 544,-84
        dc.b $E1,5
        dc.w 656,-84
        dc.b $E1,6
        dc.w 768,-84
        dc.b $E1,7
        dc.w 880,-84
        dc.b $E1,8
        dc.w 992,-84
        dc.b $E1,9
        dc.w 1104,-84
        dc.b $E1,10
        dc.w 1216,-84
        dc.b $E1,11
        dc.w 1328,-84
        dc.b $FF,0
RoomObjects:
        dc.b $E0,ActionStep
        dc.w 64,-5
        dc.b $E0,ActionRun
        dc.w 128,-5
        dc.b $E0,ActionReset
        dc.w 192,-5
        dc.b $E0,ActionInput
        dc.w 256,-5
        dc.b $E2,0
        dc.w 48,-104
        dc.b $E2,1
        dc.w 80,-104
        dc.b $E2,2
        dc.w 112,-104
        dc.b $E2,3
        dc.w 144,-104
        dc.b $E2,4
        dc.w 176,-104
        dc.b $E2,5
        dc.w 208,-104
        dc.b $E2,6
        dc.w 240,-104
        dc.b $E2,7
        dc.w 272,-104
        dc.b $E1,ReturnRing
        dc.w 400,-72
        dc.b $FF,0
        even

LabFrameHook:
        movem.l d0-d7/a0-a6,-(sp)
        addq.l #1,v_frames
        cmpi.w #120,v_age
        bhs.s .age_ok
        addq.w #1,v_age
.age_ok:
        tst.w v_room
        beq.s .objects
        bsr.w UpdateAlgorithm
.objects:
        movem.l (sp)+,d0-d7/a0-a6
        jsr ExecuteObjects
        movem.l d0-d7/a0-a6,-(sp)
        tst.w v_route
        beq.s .hud
        clr.b $FFFFFE30        ; leave checkpoints behind on a lab warp
        clr.b $FFFFB03A
        move.b #3,$FFFFFE12
        move.w #$FFFF,$FFFFB02C
        move.w v_route,d0
        subq.w #1,d0
        add.w d0,d0
        lea Routes(pc),a0
        move.w (a0,d0.w),Zone
        move.w #1,$FFFFFE02
        clr.w v_route
        bra.s .done
.hud:
        move.w sr,-(sp)
        move.w #$2700,sr
        bsr.w DrawHUD
        move.w (sp)+,sr
.done:
        movem.l (sp)+,d0-d7/a0-a6
        rts
Routes: dc.w $0000,$0200,$0400,$0100,$0300,$0500
        dc.w $0002,$0201,$0401,$0101,$0301,$0501,$0001

ObjLabSwitch:
        tst.b $24(a0)
        bne.s .active
        move.b #2,$24(a0)
        move.b #4,1(a0)
        move.w #$8000+LabTile,2(a0)
        move.l #SwitchMaps,4(a0)
        move.b #$18,$19(a0)
        move.b #2,$18(a0)
.active:
        ; The same SolidObject contact used by the template's pressure switch.
        move.w #$1B,d1
        moveq #5,d2
        moveq #5,d3
        move.w 8(a0),d4
        jsr SolidObject
        moveq #0,d0
        move.b $28(a0),d0
        cmpi.b #ActionRun,d0
        bne.s .frame
        tst.w v_running
        beq.s .frame
        moveq #ActionPause,d0
.frame:
        add.b d0,d0
        move.b d0,$1A(a0)
        tst.b $25(a0)
        beq.s .release
        addq.b #1,$1A(a0)
        tst.b $29(a0)
        bne.s .display
        move.b #1,$29(a0)
        cmpi.w #30,v_age
        blo.s .display
        movem.l d0-d7/a0-a6,-(sp)
        moveq #0,d0
        move.b $28(a0),d0
        bsr.w SwitchAction
        movem.l (sp)+,d0-d7/a0-a6
        bra.s .display
.release:
        clr.b $29(a0)
.display:
        jmp DisplaySprite

SwitchAction:
        move.w d0,v_last_action
        addq.w #1,v_action_count
        cmpi.w #ActionStep,d0
        bhs.s .room
        move.w v_gates,d1
        bset d0,d1
        move.w d1,v_gates
        move.w #$C3,d0
        jmp SoundEffect
.room:
        subi.w #ActionStep,d0
        beq.s .step
        subq.w #1,d0
        beq.s .run
        subq.w #1,d0
        beq.s .reset
        addq.w #1,v_dataset
        cmpi.w #5,v_dataset
        blo.s .reset
        clr.w v_dataset
.reset:
        bsr.w ResetWorld
        bra.s .sound
.step:
        clr.w v_running
        bsr.w BeginStep
        rts
.run:
        tst.w v_done
        bne.s .sound
        eori.w #1,v_running
        clr.w v_auto_delay
.sound:
        move.w #$CD,d0
        jmp SoundEffect

ObjLabRing:
        tst.b $24(a0)
        bne.s .active
        move.b #2,$24(a0)
        move.b #4,1(a0)
        move.w #$8000+LabTile,2(a0)
        move.l #RingMaps,4(a0)
        move.b #$30,$19(a0)
        move.b #3,$18(a0)
        move.b $28(a0),$1A(a0)
.active:
        moveq #0,d0
        move.b $28(a0),d0
        cmpi.b #ReturnRing,d0
        beq.s .open
        move.w v_gates,d1
        btst d0,d1
        beq.s .return
.open:
        cmpi.w #30,v_age
        blo.s .display
        cmpi.b #6,Sonic+$24
        bhs.s .display
        move.w Sonic+8,d1
        sub.w 8(a0),d1
        addi.w #18,d1
        cmpi.w #36,d1
        bhs.s .display
        move.w Sonic+$C,d1
        sub.w $C(a0),d1
        addi.w #24,d1
        cmpi.w #48,d1
        bhs.s .display
        addq.w #1,d0
        move.w d0,v_route
        move.w #$C3,d0
        jsr SoundEffect
.display:
        jmp DisplaySprite
.return:
        rts

ObjLabMonitor:
        tst.b $24(a0)
        bne.s .active
        move.b #2,$24(a0)
        move.b $28(a0),$27(a0) ; save index before using aligned RAM for mapping
.active:
        moveq #0,d0
        move.b $27(a0),d0
        cmpi.w #4,v_algorithm
        beq.s .jobs
        cmpi.w #5,v_algorithm
        bne.s .visible
        cmpi.w #5,d0
        bhs.w .hidden
        bra.s .visible
.jobs:
        cmpi.w #4,d0
        bhs.w .hidden
.visible:
        move.b #4,1(a0)
        move.b #$18,$19(a0)
        move.b #3,$18(a0)
        move.w #$8000+LabTile,2(a0)
        lea $28(a0),a1
        move.l a1,4(a0)
        clr.b $1A(a0)
        ; Native font, native monitor body, and a native ring marking the pair.
        move.w #2,(a1)+
        move.b #4,(a1)+
        moveq #0,d0
        move.b $27(a0),d0
        lea v_values,a2
        moveq #0,d1
        move.b (a2,d0.w),d1
        cmpi.b #$FF,d1
        bne.s .digit
        move.w #GlyphDash,d1
        bra.s .value
.digit:
        addi.w #DigitZero,d1
.value:
        move.b #-7,(a1)+
        clr.b (a1)+
        move.b #0,(a1)+       ; mappings have unaligned big-endian tile words
        move.b d1,(a1)+
        move.b #-4,(a1)+
        lea v_ids,a2
        moveq #0,d1
        move.b (a2,d0.w),d1
        addq.w #LetterA,d1
        move.b #16,(a1)+
        clr.b (a1)+
        clr.b (a1)+
        move.b d1,(a1)+
        move.b #-4,(a1)+
        move.b #-17,(a1)+
        move.b #$F,(a1)+     ; original 32x32 monitor mapping
        move.w #MonitorTile,d1
        move.w d1,d2
        lsr.w #8,d2
        move.b d2,(a1)+
        move.b d1,(a1)+
        move.b #-16,(a1)+
        move.b #-35,(a1)+
        clr.b (a1)+          ; transparent single tile when not selected
        moveq #0,d1
        cmp.w v_pair_left,d0
        beq.s .highlight
        cmp.w v_pair_right,d0
        beq.s .highlight
        tst.w v_done
        beq.s .body
        cmpi.w #2,v_algorithm
        blo.s .highlight
        cmpi.w #6,v_algorithm
        blo.s .result_marker
        cmpi.w #11,v_algorithm
        blo.s .highlight
.result_marker:
        btst d0,v_result_mask+1
        beq.s .body
.highlight:
        move.w #$2000+TokenTile,d1
        move.b #5,-1(a1)     ; original 16x16 collectible ring, palette 1
.body:
        move.w d1,d2
        lsr.w #8,d2
        move.b d2,(a1)+
        move.b d1,(a1)+
        move.b #-8,(a1)+
        move.w d0,d1
        lsl.w #5,d1
        addi.w #48,d1
        cmpi.w #4,v_algorithm
        beq.s .job_x
        cmpi.w #5,v_algorithm
        bne.s .x_ready
        move.w d0,d1
        mulu.w #48,d1
        addi.w #64,d1
        bra.s .x_ready
.job_x:
        move.w d0,d1
        lsl.w #6,d1
        addi.w #64,d1
.x_ready:
        move.w d1,8(a0)
        move.w v_row_y,$C(a0)
        cmpi.w #3,v_phase
        bne.s .display
        move.w v_pair_right,d2
        sub.w v_pair_left,d2
        move.w v_timer,d1    ; interpolate across any distance in 32 frames
        mulu.w d2,d1
        cmp.w v_pair_left,d0
        beq.s .left
        cmp.w v_pair_right,d0
        bne.s .display
        sub.w d1,8(a0)
        bra.s .arc
.left:
        add.w d1,8(a0)
.arc:
        move.w v_timer,d1
        cmpi.w #16,d1
        bls.s .offset
        neg.w d1
        addi.w #32,d1
.offset:
        cmp.w v_pair_left,d0
        beq.s .up
        add.w d1,$C(a0)
        bra.s .display
.up:
        sub.w d1,$C(a0)
.display:
        jmp DisplaySprite
.hidden:
        rts

        include "native/src/algorithms.asm"
        include "native/src/expanded.asm"
        include "native/src/hud.asm"
        include "native/assets/assets.inc"
        include "native/src/flat-zones.asm"
TileArt:
        incbin "native/assets/tiles.bin"
TileArtEnd:
        even
LabEnd:
