// lyriceng.asm — resident lyric engine (FONT-RENDER + repetition lookup).
// Loaded once at $0c00 via mkpef --music. Renders each lyric line from the C64
// charset into 8 hires sprites (24-char white-ish row, animated), using an
// ORDER table (onset -> unique-line index) so repeated choruses cost nothing.
//
// Resident data (above the SID, $1000-$3005):
//   FONT  $3100  64 glyphs x 8 = 512B
//   UNIQ  $3300  LYRIC_NUNIQ x 24 screen codes
//   ORDER $3500  LYRIC_NLINES bytes (unique-line index per onset)
//   ONSET $3580  LYRIC_NLINES x 2 (LE PAL frame)
//
// Jump table: $0c00 lyric_play / $0c03 init / $0c06 blit_line / $0c09 setup_sprites

.import source "lyric_n.asm"          // LYRIC_NLINES, LYRIC_NUNIQ
.const FONT  = $3100
.const UNIQ  = $3300
.const ORDER = $3600
.const ONSET = $3680
.const NLINES = LYRIC_NLINES
.const SID_PLAY = $1003
.const B1 = $4800
.const B2 = $8800

.const FRAME=$05      // 16-bit
.const CURSOR=$07
.const LASTLINE=$08
.const SRC=$09        // $09/$0a
.const DST1=$0b
.const DST2=$0d
.const BANKF=$0f
.const ANIM=$10
.const SLIDE=$11
.const GP=$12         // $12/$13 glyph ptr
.const DEST=$14       // $14/$15 dest ptr
.const CCOL=$16
.const TMP=$17

* = $0c00 "lyriceng"
        jmp lyric_play
        jmp init_lyric
        jmp blit_line
        jmp setup_sprites

lyric_play:
        jsr SID_PLAY
        inc FRAME
        bne adv
        inc FRAME+1
adv:
        ldx CURSOR
        cpx #NLINES-1
        bcs adv_done
        inx
        txa
        asl
        tay
        lda FRAME+1
        cmp ONSET+1,y
        bcc adv_done
        bne adv_inc
        lda FRAME
        cmp ONSET,y
        bcc adv_done
adv_inc:
        inc CURSOR
        jmp adv
adv_done:
        lda CURSOR
        cmp LASTLINE
        beq lp_anim
        sta LASTLINE
        jsr blit_line
        lda #0
        sta SLIDE              // SLIDE = per-line frame counter (fade-in)
lp_anim:
        jsr animate
        rts

init_lyric:
        ldx #0
        lda #0
ic:
        sta B1,x
        sta B1+$100,x
        sta B2,x
        sta B2+$100,x
        inx
        bne ic
        lda #0
        sta FRAME
        sta FRAME+1
        sta CURSOR
        sta ANIM
        sta SLIDE
        lda #$ff
        sta LASTLINE
        rts

// render UNIQ[ORDER[CURSOR]] into bank1 block, copy to bank2
blit_line:
        ldx #0
        lda #0
bl_clr:
        sta B1,x
        sta B1+$100,x
        inx
        bne bl_clr
        // SRC = UNIQ + ORDER[CURSOR]*24
        lda #<UNIQ
        sta SRC
        lda #>UNIQ
        sta SRC+1
        ldx CURSOR
        ldy ORDER,x            // uidx
        beq bl_go
bl_mul:
        clc
        lda SRC
        adc #24
        sta SRC
        bcc bl_m1
        inc SRC+1
bl_m1:
        dey
        bne bl_mul
bl_go:
        ldy #0                 // col 0..23
bl_col:
        sty CCOL
        lda (SRC),y            // screen code
        // GP = FONT + code*8
        sta TMP
        lda #0
        sta GP+1
        lda TMP
        asl
        rol GP+1
        asl
        rol GP+1
        asl
        rol GP+1
        clc
        adc #<FONT
        sta GP
        lda GP+1
        adc #>FONT
        sta GP+1
        // DEST = B1 + destoff[col]
        lda destlo,y
        sta DEST
        lda desthi,y
        sta DEST+1
        ldx #0                 // glyph row 0..7
bl_row:
        txa
        tay
        lda (GP),y             // glyph row (only (zp),y is valid)
        ldy #0
        sta (DEST),y           // sprite block, advancing DEST by 3/row
        clc
        lda DEST
        adc #3
        sta DEST
        bcc bl_rn
        inc DEST+1
bl_rn:
        inx
        cpx #8
        bne bl_row
        ldy CCOL
        iny
        cpy #24
        bne bl_col
        // copy bank1 block -> bank2
        ldx #0
bl_cp:
        lda B1,x
        sta B2,x
        lda B1+$100,x
        sta B2+$100,x
        inx
        bne bl_cp
        rts

animate:
        lda ANIM
        clc
        adc #3
        sta ANIM
        // gentle sine bob (per-sprite phase), no slide
        ldx #0
an_yl:
        txa
        asl
        asl
        asl
        clc
        adc ANIM
        tay
        lda sinetab,y
        clc
        adc #202
        pha
        txa
        asl
        tay
        pla
        sta $d001,y
        inx
        cpx #8
        bne an_yl
        // colour pulse: dark <-> light <-> dark via the sine on ANIM
        ldx ANIM
        lda sinetab,x
        lsr                    // 0..4
        tax
        lda faderamp,x
        ldx #7
an_cl:
        sta $d027,x
        dex
        bpl an_cl
        rts

setup_sprites:
        lda #$ff
        sta $d015
        lda #0
        sta $d01c
        sta $d01b
        sta $d017
        sta $d01d
        sta $d010
        ldx #7
        lda #1
ss_col:
        sta $d027,x
        dex
        bpl ss_col
        ldx #7
ss_xy:
        txa
        asl
        tay
        lda sprx,x
        sta $d000,y
        lda #210
        sta $d001,y
        dex
        bpl ss_xy
        lda BANKF
        bne ss_b2
        ldx #7
ss_p1:
        txa
        clc
        adc #$20
        sta $43f8,x
        dex
        bpl ss_p1
        rts
ss_b2:
        ldx #7
ss_p2:
        txa
        clc
        adc #$20
        sta $83f8,x
        dex
        bpl ss_p2
        rts

sprx:   .byte 84,108,132,156,180,204,228,252
faderamp: .byte 0,6,11,4,12            // darker pulse: black->blue->dkgrey->purple->grey
destlo: .fill 24, <(B1 + floor(i/3)*64 + 21 + (i-floor(i/3)*3))
desthi: .fill 24, >(B1 + floor(i/3)*64 + 21 + (i-floor(i/3)*3))
sinetab:
        .fill 256, round(4 + 4*sin(toRadians(i*360/256)))
