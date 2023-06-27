from music21 import *
from ziffers import *

# Parse Ziffers string to music21 object
s = to_music21('(i v vi vii^dim)@(q0 e 2 1 q 012)', scale="Lydian", time="4/4")

# See https://web.mit.edu/music21/doc/installing/installAdditional.html
# Attempt to open / show the midi in MuseScore
s.show()