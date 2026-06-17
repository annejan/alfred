# Björk - Human Behaviour. Vocal = ch4 "Vocals-Bjork" (labelled); bass = ch1
# Finger Bass; drums ch10. The signature TIMPANI (ch2) answers the vocal -> --fill 2
# drops it into her rest holes. Kit is driven by the Jingle Bell (GM 83, 1776
# hits), which needed adding to GM_DRUM (83/84 -> hihat).
F="sources/Bjork_Human_Behavior.mid"
python3 midi_to_sng.py "$F" renders/human_behaviour.sng \
  --map 4,1,- --mode clean --fill 2 --tempo 08 --title "Human Behaviour"
# ~92 bpm song -> --tempo 08 (=93.75 bpm at 1x); 236 timpani fill notes,
# kick 217 / snare 222 / hihat 441 (jingle bell).

# pack + capture. Length = rows*tempo/50 = 1847*8/50 = 295.5s = 4:55.
( cd /home/annejan/Projects/goattracker2-Qt/src && \
  qt/build/gt2reloc /home/annejan/Projects/jantje/renders/human_behaviour.sng \
                    /home/annejan/Projects/jantje/renders/human_behaviour.sid )
sidplayfp -w/tmp/bjork.wav -t300 renders/human_behaviour.sid
ffmpeg -y -t 295 -i /tmp/bjork.wav \
  -af "afade=t=in:st=0:d=0.08,afade=t=out:st=293:d=2.0,loudnorm=I=-14:TP=-1.5:LRA=11" \
  -codec:a libmp3lame -b:a 320k renders/human_behaviour.mp3
