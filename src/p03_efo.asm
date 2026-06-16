// p03_efo.asm — EFO2 header (built -binfile, cat before p03.prg).
.import source "p03.sym"
.pc = $0000 "EfoHeader"
        .text "EFO2"
        .word $0000            // prepare
        .word setup
        .word interrupt
        .word $0000            // main
        .word $0000            // fadeout
        .word $0000            // cleanup
        .word call_play            // callmusic
        .byte 'S'              // i/o safe
        .byte 'P', $09, $09    // code page(s)
        .byte 'P', $80, $87    // screen + colour stage
        .byte 'P', $a0, $bf    // bitmap
        .byte 'P', $88, $89    // sprite shape block
        .byte 'I', $0c, $0f    // resident lyric engine
        .byte 'I', $31, $3f    // resident sprite shapes
        .byte $00
