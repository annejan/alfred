#!/usr/bin/env python3
"""Per slot, extract K candidate frames across the slot's video window and
dither each to a C64 koala PREVIEW png, so vision agents rank the actual
on-screen result. Writes cand/sNN_kKK.png + cand/manifest.json."""
import json, os, subprocess
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
VID=json.load(open(os.path.join(ROOT,'clip.json')))['video']
K=8
d=json.load(open('segments.json')); SONG=d['song_len']; VL=d['video_len']; segs=d['segments']
os.makedirs('cand',exist_ok=True)
man=[]
for s in segs:
    i=s['idx']
    vt0=max(1.0, s['start']/SONG*VL); vt1=min(VL-1, s['end']/SONG*VL)
    if vt1-vt0<2: vt1=min(VL-1,vt0+2)
    cands=[]
    for k in range(K):
        t=vt0+(vt1-vt0)*k/(K-1)
        raw="/tmp/cr.png"
        # crop to the largest 4:3 region that fits (robust to any source AR:
        # 16:9 -> pillar, 5:4 -> letterbox), then scale to the C64 320x200.
        subprocess.run(["ffmpeg","-y","-ss",f"{t:.2f}","-i",VID,"-frames:v","1",
            "-vf",r"crop=min(iw\,ih*4/3):min(ih\,iw*3/4),scale=320:200",raw],
            stderr=subprocess.DEVNULL,check=True)
        prev=f"cand/s{i:02d}_k{k}.png"
        subprocess.run(["python3","tools/photo_to_koala.py",raw,"/tmp/cr.kla",
            "--preview",prev,"--bg","0","--contrast","1.15","--sat","1.25"],
            check=True,stdout=subprocess.DEVNULL)
        cands.append(dict(k=k,t=round(t,2),preview=prev))
    man.append(dict(idx=i,start=s['start'],end=s['end'],
                    video_win=[round(vt0,1),round(vt1,1)],candidates=cands))
    print(f"slot {i:2d}: {K} candidates @ {vt0:.0f}-{vt1:.0f}s")
json.dump(man,open('cand/manifest.json','w'),indent=1)
print("manifest -> cand/manifest.json")
