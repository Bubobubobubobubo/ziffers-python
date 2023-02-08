""" Methods for calculating notes from scales and list of all intervals in scales"""
#!/usr/bin/env python3
# pylint: disable=locally-disabled, no-name-in-module
import re
from math import floor
from .defaults import (
    DEFAULT_OCTAVE,
    SCALES,
    MODIFIERS,
    NOTES_TO_INTERVALS,
    INTERVALS_TO_NOTES,
    ROMANS,
    CIRCLE_OF_FIFTHS,
    CHORDS,
)


def midi_to_note_name(midi: int) -> str:
    """Creates note name from midi number

    Args:
        midi (int): Mii number

    Returns:
        str: Note name
    """
    return INTERVALS_TO_NOTES[midi % 12]


def note_name_to_interval(name: str) -> int:
    """Parse note name to interval

    Args:
        name (str): Note name as: [a-gA-G][#bs]

    Returns:
        int: Interval of the note name [-1 - 11]
    """
    items = re.match(r"^([a-gA-G])([#bs])?$", name)
    if items is None:
        return 0
    values = items.groups()
    modifier = MODIFIERS[values[1]] if values[1] else 0
    interval = NOTES_TO_INTERVALS[values[0].capitalize()]
    return interval + modifier


def note_name_to_midi(name: str) -> int:
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
    interval = NOTES_TO_INTERVALS[values[0].capitalize()]
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
    root = note_name_to_midi(root) if isinstance(root, str) else root
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


def parse_roman(numeral: str) -> int:
    """Parse roman numeral from string

    Args:
        numeral (str): Roman numeral as string

    Returns:
        int: Integer parsed from roman numeral
    """
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


def accidentals_from_note_name(name: str) -> int:
    """Generates number of accidentals from name of the note.

    Args:
        name (str): Name of the note

    Returns:
        int: Integer representing number of flats or sharps: -7 flat to 7 sharp.
    """
    idx = CIRCLE_OF_FIFTHS.index(name.upper())
    return idx - 6


def accidentals_from_midi_note(note: int) -> int:
    """Generates number of accidentals from name of the note.

    Args:
        note (int): Note as midi number

    Returns:
        int: Integer representing number of flats or sharps: -7 flat to 7 sharp.
    """
    name = midi_to_note_name(note)
    return accidentals_from_note_name(name)


def midi_to_tpc(note: int, key: str | int):
    """Return Tonal Pitch Class value for the note

    Args:
        note (int): MIDI note
        key (str | int): Key as a string (A-G) or a MIDI note.

    Returns:
        _type_: Tonal Pitch Class value for the note
    """
    if isinstance(key, str):
        acc = accidentals_from_note_name(key)
    else:
        acc = accidentals_from_midi_note(key)
    return (note * 7 + 26 - (11 + acc)) % 12 + (11 + acc)


def midi_to_pitch_class(note: int) -> int:
    """Return pitch class from midi

    Args:
        note (int): Note in midi

    Returns:
        int: Returns note % 12
    """
    return note % 12


def midi_to_octave(note: int) -> int:
    """Return octave for the midi note

    Args:
        note (int): Note in midi

    Returns:
        int: Returns default octave in Ziffers where C4 is in octave 0
    """
    return 0 if note <= 0 else floor(note / 12)


def midi_to_pc(note: int, key: str | int, scale: str) -> tuple:
    """Return pitch class and octave from given midi note, key and scale

    Args:
        note (int): Note as MIDI number
        key (str | int): Used key
        scale (str): Used scale

    Returns:
        tuple: Returns tuple containing (pitch class as string, pitch class, octave, optional modifier)
    """
    sharps = ["0", "#0", "1", "#1", "2", "3", "#3", "4", "#4", "5", "#5", "6"]
    flats = ["0", "b1", "1", "b2", "2", "3", "b4", "4", "b5", "5", "b6", "6"]
    tpc = midi_to_tpc(note, key)
    pitch_class = midi_to_pitch_class(note)
    octave = midi_to_octave(note) - 5
    if scale.upper() == "CHROMATIC":
        return (str(pitch_class), pitch_class, octave)
    if tpc >= 6 and tpc <= 12 and len(flats[pitch_class]) == 2:
        npc = flats[pitch_class]
    elif tpc >= 20 and tpc <= 26 and len(sharps[pitch_class]) == 2:
        npc = sharps[pitch_class]
    else:
        npc = sharps[pitch_class]

    if len(npc) > 1:
        return (npc, int(npc[1]), octave, 1 if (npc[0] == "#") else -1)

    return (npc, int(npc), octave)


def chord_from_roman_numeral(roman: str, name: str = "major", num_octaves: int = 1) -> list[int]:
    """Generates chord from given roman numeral and chord name

    Args:
        roman (str): Roman numeral
        name (str, optional): Chord name. Defaults to "major".
        num_octaves (int, optional): Number of octaves for the chord. Defaults to 1.

    Returns:
        list[int]: _description_
    """
    root = parse_roman(roman) - 1
    tonic = (DEFAULT_OCTAVE * 12) + root + 12
    intervals = CHORDS.get(name,CHORDS["major"])
    notes = []
    for cur_oct in range(num_octaves):
        for iterval in intervals:
            notes.append(tonic + iterval + (cur_oct * 12))
    return notes
