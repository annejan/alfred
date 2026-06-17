#!/usr/bin/env python3
"""
Detect musical section boundaries in the rendered SID and lay out the
slideshow so image cuts land on song transitions.

Method: log-mel features per ~0.25s frame -> cosine self-similarity matrix
-> Foote checkerboard-kernel novelty curve -> peak-pick the strongest
boundaries (min spacing enforced). Boundaries are snapped to the nearest
beat (tempo from onset autocorrelation) for tightness.

Each resulting segment becomes one koala image; its source video frame is
sampled at the proportional video time of the segment start, so the imagery
follows the video while the cuts follow the music.

Usage: segment.py wav video_len song_len --n N --out segments.json
"""
import sys, json, argparse
import numpy as np
from scipy.io import wavfile
from scipy.ndimage import gaussian_filter1d

def stft_mag(x, sr, n_fft=2048, hop=512):
    win = np.hanning(n_fft)
    nfr = 1 + (len(x) - n_fft) // hop
    out = np.empty((nfr, n_fft//2+1), dtype=np.float32)
    for i in range(nfr):
        fr = x[i*hop:i*hop+n_fft] * win
        out[i] = np.abs(np.fft.rfft(fr))
    return out, hop

def mel_features(x, sr):
    mag, hop = stft_mag(x, sr)
    freqs = np.fft.rfftfreq(2048, 1/sr)
    # crude mel filterbank (32 bands)
    nb = 32
    mel = lambda f: 2595*np.log10(1+f/700)
    mmin, mmax = mel(20), mel(sr/2)
    edges = np.array([700*(10**(m/2595)-1) for m in np.linspace(mmin, mmax, nb+2)])
    fb = np.zeros((nb, len(freqs)), np.float32)
    for b in range(nb):
        lo, ce, hi = edges[b], edges[b+1], edges[b+2]
        l = (freqs>=lo)&(freqs<=ce); r=(freqs>=ce)&(freqs<=hi)
        fb[b, l] = (freqs[l]-lo)/max(ce-lo,1e-9)
        fb[b, r] = (hi-freqs[r])/max(hi-ce,1e-9)
    feat = np.log1p(mag @ fb.T)         # [frames, 32]
    fps = sr/hop
    return feat, fps

def novelty(feat, kernel_sec, fps):
    # downsample to ~8 fps, z-score each band so timbre AND energy count
    step = max(1, int(round(fps/8)))
    f = feat[::step].astype(np.float64)
    nfps = fps/step
    f = (f - f.mean(0)) / (f.std(0)+1e-9)
    W = max(2, int(round(kernel_sec*nfps)))      # half-window in frames
    n = len(f)
    # cumulative sums for fast windowed means
    cs = np.vstack([np.zeros(f.shape[1]), np.cumsum(f,0)])
    def wmean(a,b): return (cs[b]-cs[a])/max(b-a,1)
    nov = np.zeros(n)
    for i in range(n):
        a0,a1 = max(0,i-W), i
        b0,b1 = i, min(n,i+W)
        if a1-a0<W//2 or b1-b0<W//2: continue
        u,v = wmean(a0,a1), wmean(b0,b1)
        nov[i] = 1 - (u@v)/((np.linalg.norm(u)*np.linalg.norm(v))+1e-9)
    nov = gaussian_filter1d(np.maximum(nov,0), nfps*0.5)
    if nov.max()>0: nov/=nov.max()
    return nov, nfps

def estimate_beat(x, sr):
    # onset envelope -> autocorrelation in 60..160 bpm -> beat period
    mag, hop = stft_mag(x, sr, 1024, 512)
    flux = np.maximum(0, np.diff(mag, axis=0)).sum(1)
    flux = gaussian_filter1d(flux, 2)
    fps = sr/512
    lo, hi = int(fps*60/160), int(fps*60/60)
    ac = np.correlate(flux, flux, 'full')[len(flux)-1:]
    lag = lo + int(np.argmax(ac[lo:hi]))
    bpm = 60*fps/lag
    # beat phase: pick offset maximizing flux on the grid
    period = lag
    best_off, best = 0, -1
    for off in range(period):
        s = flux[off::period].sum()
        if s>best: best, best_off = s, off
    phase = best_off/fps
    return bpm, 60/bpm, phase

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('wav'); ap.add_argument('video_len',type=float)
    ap.add_argument('song_len',type=float)
    ap.add_argument('--n',type=int,default=16)
    ap.add_argument('--min-sec',type=float,default=7.0)
    ap.add_argument('--kernel',type=float,default=6.0)
    ap.add_argument('--target',type=float,default=14.0,help='target sub-shot length')
    ap.add_argument('--max-split',type=float,default=22.0,help='split sections longer than this')
    ap.add_argument('--out',default='segments.json')
    a=ap.parse_args()

    sr, x = wavfile.read(a.wav)
    if x.ndim>1: x=x.mean(1)
    x = x.astype(np.float32); x/=max(1,np.abs(x).max())
    dur=len(x)/sr

    feat,fps = mel_features(x,sr)
    nov,nfps = novelty(feat,a.kernel,fps)
    # beat grid from the GoatTracker row math (tempo 8 @50Hz -> 0.16s/row,
    # 4 rows/beat = 0.64s); far more reliable here than audio autocorrelation.
    import os as _os
    _clip=json.load(open(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),'clip.json')))
    bpm,beat,phase = 60/_clip['beat'], _clip['beat'], 0.0

    # candidate peaks (local maxima), sorted by strength, min spacing
    mind = a.min_sec
    cand=[]
    for i in range(1,len(nov)-1):
        if nov[i]>=nov[i-1] and nov[i]>nov[i+1] and nov[i]>0.02:
            cand.append((nov[i], i/nfps))
    cand.sort(reverse=True)
    print(f"  [{len(cand)} candidate peaks; top strengths: "
          f"{', '.join(f'{s:.2f}@{t:.0f}s' for s,t in cand[:12])}]", file=sys.stderr)
    bounds=[]
    for _strength,t in cand:
        if t<mind or t>dur-mind: continue
        if all(abs(t-b)>=mind for b in bounds): bounds.append(t)
        if len(bounds)>=a.n-1: break
    bounds.sort()
    # snap to beat grid
    snap=lambda t:phase+round((t-phase)/beat)*beat
    bounds=[snap(t) for t in bounds]
    bounds=sorted(set(round(b,3) for b in bounds))

    starts=[0.0]+bounds
    ends=bounds+[a.song_len]
    # --- pacing: subdivide long sections into beat-aligned sub-shots so the
    # cadence stays even (~TARGET s) instead of jumping 6s->54s. Cuts still
    # land on beats; long steady sections just get >1 image. ---
    snapb=lambda t:phase+round((t-phase)/beat)*beat
    raw=[]
    for s,e in zip(starts,ends):
        dur=e-s
        n = max(1, round(dur/a.target)) if dur>a.max_split else 1
        if n==1:
            raw.append((s,e)); continue
        pts=[s]+[snapb(s+i*dur/n) for i in range(1,n)]+[e]
        pts=sorted(set(round(p,3) for p in pts))
        for i in range(len(pts)-1):
            raw.append((pts[i],pts[i+1]))
    segs=[]
    for k,(s,e) in enumerate(raw):
        sample = s + 0.30*(e-s)
        vt = min(a.video_len-1, max(1.0, sample/a.song_len*a.video_len))
        segs.append(dict(idx=k, start=round(s,3), end=round(e,3),
                         dur_frames=int(round((e-s)*50)), video_t=round(vt,3)))
    json.dump(dict(bpm=round(bpm,2),beat=round(beat,4),phase=round(phase,4),
                   song_len=a.song_len,video_len=a.video_len,segments=segs),
              open(a.out,'w'),indent=1)
    print(f"bpm~{bpm:.1f} beat={beat:.3f}s  {len(segs)} segments:")
    for s in segs:
        print(f"  #{s['idx']:2d}  {s['start']:6.1f}-{s['end']:6.1f}s "
              f"({s['dur_frames']:4d}f, {(s['end']-s['start']):4.1f}s)  vid@{s['video_t']:6.1f}s")

if __name__=='__main__':
    main()
