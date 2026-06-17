#!/usr/bin/env python3
"""
Photo -> C64 Koala multicolour bitmap (full 16-colour palette, FS dither).

Koala layout (load addr $6000), matches KickAss BF_KOALA:
  $0000-$1f3f  bitmap   (8000 bytes, 40x25 cells x 8 bytes)
  $1f40-$2327  screen   (1000 bytes: hi nibble=%01 colour, lo nibble=%10)
  $2328-$270f  colour   (1000 bytes: lo nibble=%11 colour)
  $2710        background ($d021, the shared %00 colour)

Multicolour bitmap: 160x200 logical px (each 2 hw px wide), 40x25 cells of
4x8 logical px. Per cell 4 colours: %00 global bg, %01/%10 from screen RAM
nibbles, %11 from colour RAM. We pick a global bg, then per cell choose the
best 3 of 16 palette colours, then a single global Floyd-Steinberg pass
quantises every pixel to the 4 colours of its own cell (error propagates
across cell borders -> less blockiness than per-cell dithering).

Usage:
  photo_to_koala.py in.png out.kla [--preview out.png] [--no-dither]
                                   [--bg N] [--contrast f] [--sat f]
"""
import argparse
import numpy as np
from PIL import Image, ImageEnhance

# Pepto PAL C64 palette (index = C64 colour number).
PALETTE = np.array([
    (0, 0, 0), (255, 255, 255), (136, 57, 57), (103, 182, 189),
    (139, 79, 171), (80, 175, 75), (64, 64, 173), (199, 196, 126),
    (139, 95, 41), (87, 66, 0), (191, 116, 116), (86, 86, 86),
    (128, 128, 128), (155, 226, 152), (124, 124, 219), (171, 171, 171),
], dtype=np.float64)


def best_global_bg(flat_q):
    """Most-frequent palette index over the whole image -> global bg."""
    counts = np.bincount(flat_q, minlength=16)
    return int(np.argmax(counts))


def pick_cell_palettes(img160, bg):
    """For each 4x8 cell pick the 3 palette colours (besides bg) that, with
    bg, minimise squared error over the cell's 32 pixels.

    Returns cellcols[25,40,3] of palette indices (the %01,%10,%11 colours)."""
    # squared distance from every pixel to every palette colour: [200,160,16]
    diff = img160[:, :, None, :] - PALETTE[None, None, :, :]
    d2 = np.einsum('hwpc,hwpc->hwp', diff, diff)  # [H,W,16]
    bgd = d2[:, :, bg]                            # error if pixel -> bg

    cellcols = np.zeros((25, 40, 3), dtype=np.int32)
    others = [c for c in range(16) if c != bg]
    # All 3-combos of the 15 non-bg colours = 455.
    from itertools import combinations
    combos = np.array(list(combinations(others, 3)), dtype=np.int32)  # [455,3]

    for cy in range(25):
        for cx in range(40):
            blkd = d2[cy*8:cy*8+8, cx*4:cx*4+4, :].reshape(32, 16)  # [32,16]
            bgcol = bgd[cy*8:cy*8+8, cx*4:cx*4+4].reshape(32)       # [32]
            # for each combo: per-pixel min over (the 3 combo colours + bg)
            cand = blkd[:, combos]                  # [32,455,3]
            cand_min = cand.min(axis=2)             # [32,455]
            tot = np.minimum(cand_min, bgcol[:, None]).sum(axis=0)  # [455]
            cellcols[cy, cx] = combos[int(np.argmin(tot))]
    return cellcols


def quantise(img160, bg, cellcols, dither):
    """Global FS dither; each pixel maps to the 4 colours of its cell.
    Returns idx[200,160] of palette indices actually used (one of bg + 3)."""
    H, W = 200, 160
    work = img160.copy()
    out = np.zeros((H, W), dtype=np.int32)
    for y in range(H):
        cy = y >> 3
        for x in range(W):
            cx = x >> 2
            allowed = (bg, *cellcols[cy, cx])
            px = work[y, x]
            diffs = PALETTE[list(allowed)] - px
            choice = allowed[int(np.argmin(np.einsum('ij,ij->i', diffs, diffs)))]
            out[y, x] = choice
            if dither:
                err = px - PALETTE[choice]
                if x+1 < W:            work[y, x+1] += err * (7/16)
                if y+1 < H:
                    if x > 0:          work[y+1, x-1] += err * (3/16)
                    work[y+1, x] += err * (5/16)
                    if x+1 < W:        work[y+1, x+1] += err * (1/16)
    return out


def encode_koala(idx, bg, cellcols):
    """idx[200,160] palette indices -> koala byte arrays."""
    bitmap = bytearray(8000)
    screen = bytearray(1000)
    colour = bytearray(1000)
    for cy in range(25):
        for cx in range(40):
            c1, c2, c3 = cellcols[cy, cx]            # %01,%10,%11
            screen[cy*40+cx] = ((int(c1) & 15) << 4) | (int(c2) & 15)
            colour[cy*40+cx] = int(c3) & 15
            lut = {bg: 0, int(c1): 1, int(c2): 2, int(c3): 3}
            for row in range(8):
                b = 0
                for col in range(4):
                    pix = int(idx[cy*8+row, cx*4+col])
                    b = (b << 2) | lut.get(pix, 0)
                bitmap[(cy*40+cx)*8+row] = b
    return bitmap, screen, colour


def render_preview(idx, path):
    pal = PALETTE.astype(np.uint8)
    rgb = pal[idx]                       # [200,160,3]
    img = Image.fromarray(rgb, 'RGB')
    img = img.resize((320, 200), Image.NEAREST)   # restore 2:1 px aspect
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inp'); ap.add_argument('out')
    ap.add_argument('--preview'); ap.add_argument('--no-dither', action='store_true')
    ap.add_argument('--bg', type=int, default=-1)
    ap.add_argument('--contrast', type=float, default=1.0)
    ap.add_argument('--sat', type=float, default=1.0)
    ap.add_argument('--bright', type=float, default=1.0)
    a = ap.parse_args()

    im = Image.open(a.inp).convert('RGB')
    if a.bright != 1.0:   im = ImageEnhance.Brightness(im).enhance(a.bright)
    if a.contrast != 1.0: im = ImageEnhance.Contrast(im).enhance(a.contrast)
    if a.sat != 1.0:      im = ImageEnhance.Color(im).enhance(a.sat)
    im = im.resize((160, 200), Image.LANCZOS)   # 160 logical wide, 200 tall
    img160 = np.asarray(im, dtype=np.float64)

    flat_q = np.argmin(((img160[:, :, None, :] - PALETTE[None, None, :, :])**2)
                       .sum(3), axis=2).reshape(-1)
    bg = a.bg if a.bg >= 0 else best_global_bg(flat_q)
    cellcols = pick_cell_palettes(img160, bg)
    idx = quantise(img160, bg, cellcols, not a.no_dither)
    bitmap, screen, colour = encode_koala(idx, bg, cellcols)

    with open(a.out, 'wb') as f:
        f.write(bytes([0x00, 0x60]))    # load addr $6000
        f.write(bitmap); f.write(screen); f.write(colour); f.write(bytes([bg]))
    if a.preview:
        render_preview(idx, a.preview)
    print(f"{a.inp} -> {a.out}  bg={bg}  ({len(bitmap)+2002} bytes koala)")


if __name__ == '__main__':
    main()
