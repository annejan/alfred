#!/usr/bin/env python3
"""Deterministic render of the demo (no screen capture): koala images on the
segment timeline + lyric-sprite overlay replicating lyriceng.asm (slide-in +
sine bob + colour shimmer) + SID audio. Clean 50fps MP4.

Renders at 1x with vectorised numpy, ffmpeg upscales 2x (neighbour)."""
import json, subprocess, os
import numpy as np
from PIL import Image

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
FPS=50; SONG=210.0; NF=int(SONG*FPS)
BORDER=24
W,H=320+2*BORDER, 200+2*BORDER          # 368 x 248 (1x)

PAL={1:(255,255,255),7:(199,196,126),3:(103,182,189),13:(155,226,152)}
COLPAL=[1,7,3,13]
SPRX=[84,108,132,156,180,204,228,252]
SINE=np.array([round(4+4*np.sin(i*2*np.pi/256)) for i in range(256)],dtype=np.int32)

segs=json.load(open('segments.json'))['segments']
koala=[]
for s in segs:
    im=Image.open(f"koala/img{s['idx']:02d}.png").convert('RGB').resize((320,200),Image.NEAREST)
    c=np.zeros((H,W,3),np.uint8); c[BORDER:BORDER+200,BORDER:BORDER+320]=np.asarray(im)
    koala.append((s['start'],s['end'],c))

ly=json.load(open('lyrics.json'))['lines']
onset=[int(round(t*FPS)) for t,_ in ly]
spr=open('out/lyric_spr.bin','rb').read()

# precompute per line: set-pixel (sprite_idx, local_x 0..23, local_row 0..7)
LINEPX=[]
for L in range(len(ly)):
    SI=[];LX=[];LR=[]
    if ly[L][1]:
        for s in range(8):
            for r in range(8):
                for b in range(3):
                    byte=spr[L*192+s*24+r*3+b]
                    for bit in range(8):
                        if byte&(0x80>>bit):
                            SI.append(s);LX.append(b*8+bit);LR.append(r)
    LINEPX.append((np.array(SI),np.array(LX),np.array(LR)))
SPRXA=np.array(SPRX)

def koala_at(f):
    t=f/FPS
    for a,b,arr in koala:
        if a<=t<b: return arr
    return koala[-1][2]

ff=subprocess.Popen(["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
    "-r",str(FPS),"-i","-","-i","saturday_night.mp3","-vf","scale=iw*2:ih*2:flags=neighbor",
    "-c:v","libx264","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",
    "-t",str(SONG),"-shortest","/home/annejan/Videos/saturday_night_c64.mp4"],
    stdin=subprocess.PIPE)

cursor=0;last=-1;slide=0
for f in range(NF):
    while cursor<len(onset)-1 and f>=onset[cursor+1]: cursor+=1
    if cursor!=last: last=cursor; slide=44
    frame=koala_at(f).copy()
    SI,LX,LR=LINEPX[cursor]
    if len(SI):
        anim=(f*3)&255
        spy=(200+int(SINE[anim])+slide)-50+BORDER       # sprite top (image space)
        X=(SPRXA[SI]-24)+BORDER+LX
        Y=spy+7+LR
        base=(anim>>3)&3
        cols=np.array([PAL[COLPAL[(base+s)&3]] for s in range(8)],dtype=np.uint8)
        m=(Y>=0)&(Y<H)&(X>=0)&(X<W)
        frame[Y[m],X[m]]=cols[SI[m]]
    if slide>0: slide=max(0,slide-4)
    ff.stdin.write(frame.tobytes())
    if f%2000==0: print(f"{f}/{NF}")
ff.stdin.close(); ff.wait()
print("done -> ~/Videos/saturday_night_c64.mp4")
