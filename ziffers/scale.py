""" Methods for calculating notes from scales and list of all intervals in scales"""
#!/usr/bin/env python3
# pylint: disable=locally-disabled, no-name-in-module
import re
from math import floor
from .defaults import SCALES, MODIFIERS, NOTE_TO_INTERVAL, ROMANS


def note_to_midi(name: str) -> int:
    """Parse note name to midi

    Args:
        name (str): Note name in scientific notation: [a-gA-G][#bs][1-9]

    Returns:
        int: Midi note
    """
    items = re.match(r"^([a-gA-G])([#bs])?([1-9])?$", name)
    if items is None:
        return 60
    values = items.groups()
    octave = int(values[2]) if values[2] else 4
    modifier = MODIFIERS[values[1]] if values[1] else 0
    interval = NOTE_TO_INTERVAL[values[0].capitalize()]
    return 12 + octave * 12 + interval + modifier


def get_scale(name: str) -> list[int]:
    """Get a scale from the global scale list

    Args:
        name (str): Name of the scale as named in https://allthescales.org/

    Returns:
        list: List of intervals in the scale
    """
    scale = SCALES.get(name.lower().capitalize(), SCALES["Chromatic"])
    return list(map(int, str(scale)))


# pylint: disable=locally-disabled, too-many-arguments
def note_from_pc(
    root: int | str,
    pitch_class: int,
    intervals: str | list[int | float],
    cents: bool = False,
    octave: int = 0,
    modifier: int = 0,
) -> int:
    """Resolve a pitch class into a note from a scale

    Args:
        root (int | str): Root of the scale in MIDI or scientific pitch notation
        pitch_class (int): Pitch class to be resolved
        intervals (str | list[int  |  float]): Name or Intervals for the scale
        cents (bool, optional): Flag for interpreting intervals as cents. Defaults to False.
        octave (int, optional): Default octave. Defaults to 0.
        modifier (int, optional): Modifier for the pitch class (#=1, b=-1). Defaults to 0.

    Returns:
        int: Resolved MIDI note
    """

    # Initialization
    root = note_to_midi(root) if isinstance(root, str) else root
    intervals = get_scale(intervals) if isinstance(intervals, str) else intervals
    intervals = list(map(lambda x: x / 100), intervals) if cents else intervals
    scale_length = len(intervals)

    # Resolve pitch classes to the scale and calculate octave
    if pitch_class >= scale_length or pitch_class < 0:
        octave += floor(pitch_class / scale_length)
        pitch_class = (
            scale_length - (abs(pitch_class) % scale_length)
            if pitch_class < 0
            else pitch_class % scale_length
        )
        if pitch_class == scale_length:
            pitch_class = 0

    # Computing the result
    note = root + sum(intervals[0:pitch_class])

    return note + (octave * sum(intervals)) + modifier


def parse_roman(numeral: str):
    """Parse roman numeral from string"""
    values = [ROMANS[val] for val in numeral]
    result = 0
    i = 0
    while i < len(values):
        if i < len(values) - 1 and values[i + 1] > values[i]:
            result += values[i + 1] - values[i]
            i += 2
        else:
            result += values[i]
            i += 1
    return result
