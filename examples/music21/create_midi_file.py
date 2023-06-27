from music21 import *
from ziffers import *


# Create melody string
melody = "q 0 2 4 r e 1 4 3 2 s 0 1 2 6 e 2 8 2 1 h 0"
#bass_line = "(q 0 2 4 6 e 1 4 3 2 s 0 1 2 6 e 2 8 2 1 h 0)-7"

# Parse ziffers notation to melody from string
parsed = zparse(melody)
#parsed_bass = zparse(bass_line)

# Convert to music21 object
s2 = to_music21(parsed, time="4/4")

# Merge melody and bass line
#s2.append(to_music21(parsed_bass, time="4/4"))

# Write to midi file under examples/music21/midi folder
s2.write('midi', fp='examples/music21/output/ziffers_example.mid')