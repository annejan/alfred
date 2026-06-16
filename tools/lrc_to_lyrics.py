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

LRC = "Saturday Night.lrc"
# --- timing anchor (FILL IN from final SID) ---
V0_LRC, S0_SID, RATIO = 0.0, 0.0, 0.8667   # studio 130bpm -> SID 150bpm
MAXC, MAXLINES = 24, 80

# long lines -> <=24 readable forms (keep the words; the DA-BA scat shortened)
ABBR = {
 "I FEEL THE AIR IS GETTING HOT": None,            # None => split at word boundary
 "YOU KNOW I'LL TAKE YOU TO THE TOP": "I'LL TAKE YOU TO THE TOP",
 "IT'S PARTY TIME AND NOT ONE MINUTE WE CAN LOSE": None,
 "DA BA DA DAM DEE DEE DEE DA DEE DA DA DAM": "DA BA DA DAM DEE DEE",
}
def clean(s):
    s=re.sub(r'\(.*?\)','',s).replace(',','').upper().strip()
    s=re.sub(r'\s+',' ',s)
    return s
def fit(s):
    if s in ABBR and ABBR[s]: return [ABBR[s]]
    if len(s)<=MAXC: return [s]
    cut=s.rfind(' ',0,MAXC+1)
    return [s[:cut], s[cut+1:]] if cut>0 else [s[:MAXC]]

ent=[]
for l in open(LRC,encoding='utf-8'):
    m=re.match(r'\[(\d+):(\d+\.\d+)\]\s*(.*)',l)
    if not m: continue
    t=int(m.group(1))*60+float(m.group(2)); txt=clean(m.group(3))
    st=round(S0_SID+(t-V0_LRC)*RATIO,1)
    if not txt: ent.append((st,"")); continue
    parts=fit(txt)
    ent.append((st,parts[0]))
    if len(parts)>1: ent.append((round(st+1.3,1),parts[1]))

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
