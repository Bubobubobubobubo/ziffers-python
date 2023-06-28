'''Simple example of using SonicSynth to play Ziffers melody.'''
from sonicsynth import *
from ziffers import *
import numpy as np

melody = zparse("(q 0 4 2 5 e 3 9 4 2 s 5 3 1 6 8 3 4 5 2 1 q 0)+(0 3 -2 4 2)", key="E3", scale="Aerathitonic")

def build_waveform(melody, bpm):
    for item in melody.evaluated_values:
        if isinstance(item, Pitch):
            time_in_seconds = item.duration * 4 * 60 / bpm
            yield generate_square_wave(frequency=item.freq, amplitude=0.25, duration=time_in_seconds)

waveform = np.concatenate(list(build_waveform(melody,130)))

player = Playback(44100)
player.play(waveform)
