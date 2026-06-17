#!/usr/bin/env python3
"""Generic .lrc -> lyrics.json on the SID timeline (Saturday Night branch).

Parses a timed LRC, cleans/abbreviates to <=24 chars, splits long lines,
dedups consecutive repeats (eurodance choruses repeat a lot), inserts blank
markers at instrumental gaps, caps to MAXLINES (sprite-engine budget), and
maps studio LRC time -> SID time via an anchor + scale.

Set V0_LRC/S0_SID/RATIO from the final SID before running (first-vocal anchor +
SID-vocal-span / LRC-vocal-span). Until known, 1:1 (RATIO=1, S0=V0) is a
placeholder — rescale after the SID lands.
"""
import re, json, sys

CLIP=json.load(open('clip.json'))          # run from repo root
LRC=CLIP['lrc']
V0_LRC, S0_SID, RATIO = 0.0, 0.0, CLIP['ratio']   # ratio=1 if LRC already timed to render
MAXC, MAXLINES = 24, 80
ABBR=CLIP.get('abbr',{})                   # long lines -> <=24 (null => split)
_b=CLIP.get('build')                       # optional chorus build-up
SAT      = _b['match']   if _b else None
SATBUILD = _b['seq']     if _b else []
SATRESOLVE = _b['resolve'] if _b else ""
def clean(s):
    s=re.sub(r'\(.*?\)','',s).replace(',','').upper().strip()
    s=re.sub(r'\s+',' ',s)
    return s
def fit(s):
    # abbr maps a phrase -> <=24 form (or "" / None to drop it entirely)
    if s in ABBR:
        if not ABBR[s]: return []
        s=ABBR[s]
    if len(s)<=MAXC: return [s]
    cut=s.rfind(' ',0,MAXC+1)
    if cut<=0: return [s[:MAXC]]
    a,b=s[:cut],s[cut+1:]
    rest=fit(b)                       # recurse: LRC may cram several phrases per line
    if not rest and len(b)<=4: return [a]   # drop tiny orphan tail
    return [a]+rest

# parse rows, then apply the Saturday build
rows=[]
for l in open(LRC,encoding='utf-8'):
    m=re.match(r'\[(\d+):(\d+\.\d+)\]\s*(.*)',l)
    if not m: continue
    rows.append((int(m.group(1))*60+float(m.group(2)), clean(m.group(3))))
c=0
for i,(t,txt) in enumerate(rows):
    if SAT and txt==SAT:
        nxt=rows[i+1][1] if i+1<len(rows) else ""
        if nxt==SAT: rows[i]=(t,SATBUILD[c%len(SATBUILD)]); c+=1
        else: rows[i]=(t,SATRESOLVE); c=0
    else: c=0

ent=[]
for t,txt in rows:
    st=round(S0_SID+(t-V0_LRC)*RATIO,1)
    if not txt: ent.append((st,"")); continue
    parts=fit(txt)
    if not parts: ent.append((st,"")); continue
    for j,p in enumerate(parts):
        ent.append((round(st+1.3*j,1),p))

# clear lingering text during instrumental gaps: if a line is followed by a
# >GAP-second hole, drop a blank ~HOLD s after it so it doesn't linger forever.
GAP,HOLD=4.0,3.0
gapped=[]
for i,(st,txt) in enumerate(ent):
    gapped.append((st,txt))
    nxt=ent[i+1][0] if i+1<len(ent) else st+999
    if txt and nxt-st>GAP:
        gapped.append((round(min(st+HOLD, nxt-0.3),1),""))
ent=gapped

# dedup consecutive identical (incl. blanks), keep increasing time
ded=[]
for st,txt in ent:
    if ded and ded[-1][1]==txt: continue
    ded.append((st,txt))
fix=[]
for st,txt in ded:
    if fix and st<=fix[-1][0]: st=round(fix[-1][0]+0.3,1)
    fix.append((st,txt))
if fix[0][0]>0.5: fix=[(0.0,"")]+fix
# cap: drop interior blanks first, then shortest
while len(fix)>MAXLINES:
    bi=[i for i,(_,t) in enumerate(fix) if t=="" and 0<i<len(fix)-1]
    if bi: del fix[bi[len(bi)//2]]
    else:
        j=min(range(1,len(fix)),key=lambda i:len(fix[i][1]) or 99); del fix[j]

if __name__=='__main__' and '--dry' in sys.argv:
    print(f"{len(fix)} lines, max {max(len(t) for _,t in fix)} chars (cap {MAXLINES})")
    for t,x in fix: print(f"  {t:6.1f}  {x}")
else:
    json.dump({"comment":"Saturday Night LRC->SID","lines":[[t,x] for t,x in fix]},
              open('lyrics.json','w'),indent=1)
    print(f"{len(fix)} lines, max {max(len(t) for _,t in fix)} chars")
