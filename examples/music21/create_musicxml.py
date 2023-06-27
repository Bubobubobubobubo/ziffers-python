from music21 import *
from ziffers import *

# Parse ziiffers object to music21 object
parsed = zparse("q 1 024 5 235 h 02345678{12} 0", key='C', scale='Zyditonic')
s2 = to_music21(parsed,time="4/4")

# Save to MusicXML file
s2.write('musicxml', fp='examples/music21/output/ziffers_example.xml')