# Ace of Base - The Sign (Soft Karaoke MIDI, labelled tracks). CLEAN default
# (saw lead) -> the vocal melody cuts through, no mud. lead = ch1 "Melody"
# (99% lyric-align), bass = ch4 "Bass", harmony = ch8 "Whistle". 97 bpm ->
# tempo 08 (~94). Vocal enters ~0:34 (long intro). 4:20 (MIDI repeats).
M="sources/Ace of Base-18/The Sign.mid"
python3 midi_to_sng.py "$M" renders/the_sign.sng \
  --map 1,4,8 --mode shared --tempo 08 --title "The Sign"
( cd /home/annejan/Projects/goattracker2-Qt/src && \
  /home/annejan/Projects/goattracker2-Qt/qt/build/gt2reloc \
    /home/annejan/Projects/jantje/renders/the_sign.sng \
    /home/annejan/Projects/jantje/renders/the_sign.sid )
sidplayfp -w/tmp/sign.wav -t260 renders/the_sign.sid
ffmpeg -y -t 260 -i /tmp/sign.wav \
  -af "afade=t=in:st=0:d=0.08,afade=t=out:st=258:d=2.0,loudnorm=I=-14:TP=-1.5:LRA=11" \
  -codec:a libmp3lame -b:a 320k renders/the_sign.mp3
# LRC: MUST force --vocal-channel 1 (the Melody track) — auto-detect picked the
# wrong channel (ch7 Chords, similar note count) and clustered the timestamps.
python3 sng_to_lrc.py renders/the_sign.sng "$M" renders/the_sign.lrc \
  --vocal-channel 1 --title "The Sign" --artist "Ace of Base"
