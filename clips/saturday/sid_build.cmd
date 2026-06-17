# Whigfield - Saturday Night (karaoke MIDI). Vocal = ch4 "Melody" (the labelled
# one, NOT the auto-guess ch3 organ). Bass = ch5 SynBass, drums ch10.
# KEEPER (user: "deze houden we zo"). 150 bpm (tempo 05; original 130, 1x can't hit
# it). Intro riff (E-4 E-4 D#4 D#4 G#4) lifted +1 octave via --lead-8va-rows 46.
F="sources/Wigfield_Saturday_Night.mid"
python3 midi_to_sng.py "$F" renders/saturday_night.sng \
  --map 4,5,- --mode clean --fill 3 --tempo 05 --lead-8va-rows 46 --title "Saturday Night"
# DRUM/SYNTH design baked into midi_to_sng.py this session:
#   KICK  = BONK: filtered PULSE pitch-drop (E2->A1->E1), static pulse-width (no chirp)
#   SNARE = fat NOISE clap (~A#3) + light low-pass "fwip" (clap_filter)
#   HIHAT = short HIGH noise tick (own wavetable, abs ~note 90)
#   LEAD/BASS = pulse + slow PWM "flanger" (movement, frees the shared filter for drums)
#   LEAD release shortened (sr $F8->$F2) so notes stop clean (no soft hang)
# clean = lead | bass | drums; --fill 3 drops the ch3 organ hook into the vocal holes.
( cd /home/annejan/Projects/goattracker2-Qt/src && \
  /home/annejan/Projects/goattracker2-Qt/qt/build/gt2reloc \
    /home/annejan/Projects/jantje/renders/saturday_night.sng \
    /home/annejan/Projects/jantje/renders/saturday_night.sid )
# NOTE: real content runs to 3:36 (last note-on tick 51840 -> 51840/240s). sidplayfp
# reports "Song Length 3:30" but that clips the outro -> capture the FULL 3:38.
sidplayfp -w/tmp/sat.wav -t220 renders/saturday_night.sid
ffmpeg -y -t 218 -i /tmp/sat.wav \
  -af "afade=t=in:st=0:d=0.08,afade=t=out:st=216:d=2.0,loudnorm=I=-14:TP=-1.5:LRA=11" \
  -codec:a libmp3lame -b:a 320k renders/saturday_night.mp3
# LRC (synced to THIS mp3): lyric KAR-text ticks from the MIDI -> our render time =
# tick/240 s (24 ticks/16th * 0.1s/row at tempo 05). Verified: first lyric tick 936
# = row 39 = 3.9s, the exact row the lead riff enters. -> renders/saturday_night.lrc
