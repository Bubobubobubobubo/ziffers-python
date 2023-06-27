from music21 import *
from ziffers import *

# Parse ziiffers object to music21 object
parsed = zparse('1 2 qr e 124')
s2 = to_music21(parsed,time="4/4")

# Save object as png file
s2.write("musicxml.png", fp="examples/music21/output/example.png")