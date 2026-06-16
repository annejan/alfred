#!/usr/bin/env python3
"""Lyric assets: font-render engine + repetition lookup table.

Most songs repeat lines (choruses). So we store each UNIQUE line once and an
ORDER table (one byte per onset -> unique-line index), like a tracker
orderlist. The engine renders UNIQUE[ORDER[cursor]] from the C64 charset, so
line count is unlimited and RAM stays tiny.

Outputs: out/lyric_font.bin (512B charset, screen codes 0..63),
         out/lyric_uniq.bin (U*24 screen codes),
         out/lyric_order.bin (N bytes), out/lyric_onset.bin (N*2 LE frames),
         src/lyric_n.asm (.const LYRIC_NLINES, LYRIC_NUNIQ). Prints counts.
"""
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
os.makedirs('out',exist_ok=True)
ROM=open("/home/annejan/.local/share/vice/C64/chargen-901225-01.bin",'rb').read()
FONT=ROM[:64*8]

def sc(ch):
    if ch==' ': return 32
    if 'A'<=ch<='Z': return ord(ch)-64
    if '0'<=ch<='9': return ord(ch)-48+48
    return {',':44,"'":39,'.':46,'!':33,'?':63,'-':45,'(':40,')':41}.get(ch,32)
def codes(txt):
    c=[sc(ch) for ch in txt.upper()[:24]]; return bytes(c+[32]*(24-len(c)))

d=json.load(open('lyrics.json'))['lines']
uniq=[]; idx={}; order=bytearray(); onset=bytearray()
for t,txt in d:
    key=txt.upper()[:24]
    if key not in idx: idx[key]=len(uniq); uniq.append(key)
    order.append(idx[key])
    fr=int(round(t*50)); onset+=bytes([fr&0xff,(fr>>8)&0xff])
uniqbin=b''.join(codes(u) for u in uniq)
open('out/lyric_font.bin','wb').write(FONT)
open('out/lyric_uniq.bin','wb').write(uniqbin)
open('out/lyric_order.bin','wb').write(bytes(order))
open('out/lyric_onset.bin','wb').write(onset)
open('src/lyric_n.asm','w').write(f".const LYRIC_NLINES = {len(d)}\n.const LYRIC_NUNIQ = {len(uniq)}\n")
print(f"NLINES={len(d)} NUNIQ={len(uniq)}  font=512 uniq={len(uniqbin)}B order={len(order)}B onset={len(onset)}B")
