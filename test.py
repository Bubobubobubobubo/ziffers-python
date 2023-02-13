from ziffers import *
from music21 import *

z = z('e (1 2 3)+(4 2 1)*2')
s = to_music21(z,octave=-2,time="3/4")

s.show()
s.show('midi')
