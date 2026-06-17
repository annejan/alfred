"""Unit tests for the koala encoder (tools/photo_to_koala.py).

Koala layout: 8000B bitmap + 1000B screen + 1000B colour + 1 bg byte. Each 4x8
cell has 4 colours: %00 global bg, %01/%10 from screen nibbles, %11 from colour."""
import numpy as np
import photo_to_koala as K


def _cellcols():
    # every cell uses palette indices (1, 2, 3) for %01 / %10 / %11
    return np.tile(np.array([1, 2, 3], np.int32), (25, 40, 1))


def test_encode_sizes_and_all_bg():
    idx = np.zeros((200, 160), np.int32)          # every pixel = bg (0)
    bitmap, screen, colour = K.encode_koala(idx, 0, _cellcols())
    assert (len(bitmap), len(screen), len(colour)) == (8000, 1000, 1000)
    assert set(bitmap) == {0}                     # all %00


def test_encode_screen_colour_nibbles():
    idx = np.zeros((200, 160), np.int32)
    _, screen, colour = K.encode_koala(idx, 0, _cellcols())
    assert screen[0] == (1 << 4) | 2              # hi nibble=%01 col, lo=%10 col
    assert colour[0] == 3                          # %11 col


def test_encode_pixel_bitpairs():
    idx = np.zeros((200, 160), np.int32)
    idx[0, 0] = 1   # %01
    idx[0, 1] = 2   # %10
    idx[0, 2] = 3   # %11
    idx[0, 3] = 0   # %00 (bg)
    bitmap, _, _ = K.encode_koala(idx, 0, _cellcols())
    # first byte = row 0 of cell 0: pix0 pix1 pix2 pix3 packed 2 bits each
    assert bitmap[0] == 0b01_10_11_00


def test_palette_is_16_rgb():
    assert K.PALETTE.shape == (16, 3)
