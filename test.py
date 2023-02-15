from music21 import *
from sardine import *
from ziffers import *

a = zparse('1 2 qr 124')
print(list(a))
s = to_music21('1 2 qr 124',octave=-2,time="3/4")

s.show()
s.show('midi')
