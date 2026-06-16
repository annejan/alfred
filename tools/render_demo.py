#!/usr/bin/env python3
"""Deterministic render replicating the FONT-RENDER lyric engine:
koala images on the segment timeline + lyric text rendered from the C64
charset (font+uniq+order lookup) with a per-line luminance fade-in and a
gentle per-sprite sine bob + the mastered mp3 audio. Clean 50fps MP4.

Renders at 1x (vectorised numpy), ffmpeg upscales 2x."""
import json, subprocess, os
import numpy as np
from PIL import Image

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
FPS=50; SONG=210.0; NF=int(SONG*FPS)
BORDER=24; W,H=320+2*BORDER, 200+2*BORDER
AUDIO="saturday_night.mp3"

PEPTO=[(0,0,0),(255,255,255),(136,57,57),(103,182,189),(139,79,171),(80,175,75),
(64,64,173),(199,196,126),(139,95,41),(87,66,0),(191,116,116),(86,86,86),
(128,128,128),(155,226,152),(124,124,219),(171,171,171)]
FADERAMP=[0,11,12,15,1]                       # matches engine
SPRX=[84,108,132,156,180,204,228,252]
SINE=np.array([round(4+4*np.sin(i*2*np.pi/256)) for i in range(256)],dtype=np.int32)

segs=json.load(open('segments.json'))['segments']
koala=[]
for s in segs:
    im=Image.open(f"koala/img{s['idx']:02d}.png").convert('RGB').resize((320,200),Image.NEAREST)
    c=np.zeros((H,W,3),np.uint8); c[BORDER:BORDER+200,BORDER:BORDER+320]=np.asarray(im)
    koala.append((s['start'],s['end'],c))
def koala_at(f):
    t=f/FPS
    for a,b,arr in koala:
        if a<=t<b: return arr
    return koala[-1][2]

font=open('out/lyric_font.bin','rb').read()
uniq=open('out/lyric_uniq.bin','rb').read()
order=open('out/lyric_order.bin','rb').read()
on=open('out/lyric_onset.bin','rb').read()
onset=[on[i]|(on[i+1]<<8) for i in range(0,len(on),2)]
NUNIQ=len(uniq)//24

UPIX=[]
for u in range(NUNIQ):
    S=[];LX=[];R=[]
    for col in range(24):
        code=uniq[u*24+col]
        for r in range(8):
            b=font[code*8+r]
            for bit in range(8):
                if b&(0x80>>bit):
                    S.append(col//3); LX.append((col%3)*8+bit); R.append(r)
    UPIX.append((np.array(S),np.array(LX),np.array(R)))
SPRXA=np.array(SPRX)

ff=subprocess.Popen(["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
    "-r",str(FPS),"-i","-","-i",AUDIO,"-vf","scale=iw*2:ih*2:flags=neighbor",
    "-c:v","libx264","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",
    "-t",str(SONG),"-shortest","/home/annejan/Videos/saturday_night_c64.mp4"],
    stdin=subprocess.PIPE)

cursor=0
for f in range(NF):
    while cursor<len(onset)-1 and f>=onset[cursor+1]: cursor+=1
    frame=koala_at(f).copy()
    uidx=order[cursor]
    S,LX,R=UPIX[uidx]
    if len(S):
        anim=(f*3)&255
        lvl=min((f-onset[cursor])//2,4)
        col=np.array(PEPTO[FADERAMP[lvl]],dtype=np.uint8)
        spy=202+SINE[(anim+np.arange(8)*8)&255]-50+BORDER
        Y=spy[S]+7+R
        X=(SPRXA[S]-24)+BORDER+LX
        m=(Y>=0)&(Y<H)&(X>=0)&(X<W)
        frame[Y[m],X[m]]=col
    ff.stdin.write(frame.tobytes())
    if f%2500==0: print(f"{f}/{NF}")
ff.stdin.close(); ff.wait()
print("done -> ~/Videos/saturday_night_c64.mp4")
