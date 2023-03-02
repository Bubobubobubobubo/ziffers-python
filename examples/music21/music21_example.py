from music21 import *
from sardine import *
from ziffers import *


s = to_music21('(i v vi vii^dim)@(q0 e2 s1 012)',time="4/4")

s.show('midi')