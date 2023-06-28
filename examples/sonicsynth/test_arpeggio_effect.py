'''Testing arpeggio effect with sonicsynth and ziffers'''
from sonicsynth import *
from ziffers import *
import numpy as np

melody = zparse("(q 0 024 2 246 e 4 2 6 2 q 5 0)+(0 3 1 2)", key="D4", scale="Minor")

def build_waveform(melody, bpm):
    for item in melody.evaluated_values:
        if isinstance(item, Pitch):
            time_in_seconds = item.duration * 4 * 60 / bpm
            yield generate_sine_wave(frequency=item.freq, amplitude=0.5, duration=time_in_seconds)
        elif isinstance(item, Chord):
            time_in_seconds = item.durations[0] * 4 * 60 / bpm
            for pitch in item.pitch_classes:
                # Create "NES arpeggio effect"
                for i in range(1,len(item.durations)):
                    yield generate_sine_wave(frequency=pitch.freq, amplitude=0.5, duration=time_in_seconds/(len(item.durations)*3))

waveform = np.concatenate(list(build_waveform(melody,180)))

player = Playback(44100)
player.play(waveform)