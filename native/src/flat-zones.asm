; Flat foregrounds built exclusively from each zone's original blocks.
; Keep the native background layout, parallax, palettes and collision index.
; Hub width 1536; demo width 768. GHZ floor/camera 960/768; others 640/448.
LabLayout:
        lea $FFFFA400,a0
        moveq #0,d0
        move.w #$1FF,d1
.clear:
        move.l d0,(a0)+
        dbf d1,.clear
        lea $FFFFA440,a3
        moveq #2,d1
        jsr $93F2            ; original background layout loader
        lea $FFFFA580,a0     ; GHZ foreground chunk row 3
        tst.b Zone
        beq.s .select
        lea $FFFFA500,a0     ; other foregrounds use chunk row 2
.select:
        moveq #0,d0
        move.b Zone,d0
        lea FloorChunks(pc),a1
        move.b (a1,d0.w),d0
.floor:
        moveq #2,d1
        cmpi.w #$0001,Zone
        bne.s .width_ready
        moveq #5,d1
.width_ready:
        move.b d0,(a0)
        addq.b #1,d0
        move.b d0,$80(a0)
        subq.b #1,d0
        addq.w #1,a0
        dbf d1,.width_ready
        rts
FloorChunks:
        dc.b GHZFloorChunk,LZFloorChunk,MZFloorChunk,SLZFloorChunk,SYZFloorChunk,SBZFloorChunk
        even

GHZChunks:
        incbin "native/assets/ghz-chunks.bin"
MZChunks:
        incbin "native/assets/mz-chunks.bin"
LZChunks:
        incbin "native/assets/lz-chunks.bin"
SLZChunks:
        incbin "native/assets/slz-chunks.bin"
SYZChunks:
        incbin "native/assets/syz-chunks.bin"
SBZChunks:
        incbin "native/assets/sbz-chunks.bin"
        even
