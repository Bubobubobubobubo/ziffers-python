from music21 import *
from ziffers import *

# Create melody string
melody = "q 0 2 4 r e 1 4 3 2 s 0 1 2 6 e 2 8 2 1 h 0"
bass_line = "(q 0 2 4 6 e 1 4 3 2 s 0 1 2 6 e 2 8 2 1 h 0)-(7)"

# Parse ziffers notation to melody from string
parsed = zparse(melody)
parsed_bass = zparse(bass_line)

# Convert to music21 objects
part1 = to_music21(parsed, time="4/4")
part2 = to_music21(parsed_bass, time="4/4")

# Add instruments
part1.insert(instrument.Piano())
part2.insert(instrument.Soprano())

# Create score
song = stream.Score()
song.insert(0,part1)
song.insert(0,part2)

# Write to midi file under examples/music21/midi folder
song.write('midi', fp='examples/music21/output/ziffers_example.mid')