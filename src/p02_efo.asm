// p02_efo.asm — EFO2 header (built -binfile, cat before p02.prg).
.import source "p02.sym"
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
        .byte 'P', $08, $08    // code page(s)
        .byte 'P', $40, $47    // screen + colour stage
        .byte 'P', $60, $7f    // bitmap
        .byte 'P', $48, $49    // sprite shape block
        .byte 'I', $0c, $0f    // resident lyric engine
        .byte 'I', $31, $3f    // resident sprite shapes
        .byte 'I', $c0, $cf    // resident sprite-shape overflow
        .byte $00
