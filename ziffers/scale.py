""" Methods for calculating notes from scales and list of all intervals in scales"""
#!/usr/bin/env python3
# pylint: disable=locally-disabled, no-name-in-module
import re
from math import log2
from itertools import islice
from .generators import gen_primes
from .common import repeat_text
from .defaults import (
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


def midi_to_freq(note: int) -> float:
    """Transform midi to frequency"""
    freq = 440  # Frequency of A
    return (freq / 32) * (2 ** ((note - 9) / 12))


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


def get_scale(scale: str) -> list[int]:
    """Get a scale from the global scale list

    Args:
        name (str): Name of the scale as named in https://allthescales.org/

    Returns:
        list: List of intervals in the scale
    """
    if isinstance(scale, (list, tuple)):
        return scale

    scale = SCALES.get(scale.lower().capitalize(), SCALES["Ionian"])
    return scale


def get_scale_notes(name: str, root: int = 60, num_octaves: int = 1) -> list[int]:
    """Return notes for the scale

    Args:
        name (str): Name of the scale
        root (int, optional): Root note. Defaults to 60.
        num_octaves (int, optional): Number of octaves. Defaults to 1.

    Returns:
        list[int]: List of notes
    """
    scale = get_scale(name)
    scale_notes = [root]
    for _ in range(num_octaves):
        scale_notes = scale_notes + [root := root + semitone for semitone in scale]
    return scale_notes


def get_chord_from_scale(
    degree: int,
    root: int = 60,
    scale: str | tuple = "Major",
    num_notes: int = 3,
    skip: int = 2,
) -> list[int]:
    """Generate chord from the scale by skipping notes

    Args:
        degree (int): Degree of scale to start on
        root (int, optional): Root for the scale. Defaults to 60.
        scale (str, optional): Name of the scale. Defaults to "Major".
        num_notes (int, optional): Number of notes. Defaults to 3.
        skip (int, optional): Takes every n from the scale. Defaults to 2.

    Returns:
        list[int]: List of midi notes
    """
    if isinstance(scale, str):
        scale_length = get_scale_length(scale)
    else:
        scale_length = len(scale)

    num_of_octaves = ((num_notes * skip + degree) // scale_length) + 1
    scale_notes = get_scale_notes(scale, root, num_of_octaves)
    return scale_notes[degree - 1 :: skip][:num_notes]


def get_scale_length(scale: str) -> int:
    """Get length of the scale

    Args:
        name (str): Name of the scale

    Returns:
        int: Length of the scale
    """
    if isinstance(scale, (list, tuple)):
        return len(scale)

    return len(SCALES.get(scale.lower().capitalize(), SCALES["Ionian"]))

# pylint: disable=locally-disabled, too-many-arguments
def note_from_pc(
    root: int | str,
    pitch_class: int,
    intervals: str | tuple[int | float],
    octave: int = 0,
    modifier: int = 0,
    degrees: bool = False
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
    pitch_class = pitch_class-1 if degrees and pitch_class>0 else pitch_class
    root = note_name_to_midi(root) if isinstance(root, str) else root
    intervals = get_scale(intervals) if isinstance(intervals, str) else intervals
    scale_length = len(intervals)

    # Resolve pitch classes to the scale and calculate octave
    if pitch_class >= scale_length or pitch_class < 0:
        octave += pitch_class // scale_length
        pitch_class = (
            scale_length - (abs(pitch_class) % scale_length)
            if pitch_class < 0
            else pitch_class % scale_length
        )
        if pitch_class == scale_length:
            pitch_class = 0

    # Computing the result
    note = root + sum(intervals[0:pitch_class])

    note = note + (octave * sum(intervals)) + modifier

    if isinstance(note, float):
        return resolve_pitch_bend(note)

    return (note, None)


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
    if name not in CIRCLE_OF_FIFTHS:
        name = midi_to_note_name(note_name_to_midi(name))

    idx = CIRCLE_OF_FIFTHS.index(name)
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
        acc = accidentals_from_note_name(key[0])
    else:
        acc = accidentals_from_midi_note(key)
    return (note * 7 + 26 - (11 + acc)) % 12 + (11 + acc)


def midi_to_octave(note: int) -> int:
    """Return octave for the midi note

    Args:
        note (int): Note in midi

    Returns:
        int: Returns default octave in Ziffers where C4 is in octave 0
    """
    return 0 if note <= 0 else note // 12


def midi_to_pitch_class(note: int, key: str | int, scale: str) -> dict:
    """Return pitch class and octave from given midi note, key and scale

    Args:
        note (int): Note as MIDI number
        key (str | int): Used key
        scale (str): Used scale

    Returns:
        tuple: Returns dict containing pitch-class values
    """
    pitch_class = int(note % 12)  # Cast to int "fixes" microtonal scales
    octave = midi_to_octave(note) - 5
    if isinstance(scale, str) and scale.upper() == "CHROMATIC":
        return {"text": str(pitch_class), "pitch_class": pitch_class, "octave": octave}

    sharps = ["0", "#0", "1", "#1", "2", "3", "#3", "4", "#4", "5", "#5", "6"]
    flats = ["0", "b1", "1", "b2", "2", "3", "b4", "4", "b5", "5", "b6", "6"]
    tpc = midi_to_tpc(note, key)
    if tpc >= 6 and tpc <= 12 and len(flats[pitch_class]) == 2:
        npc = flats[pitch_class]
    elif tpc >= 20 and tpc <= 26 and len(sharps[pitch_class]) == 2:
        npc = sharps[pitch_class]
    else:
        npc = sharps[pitch_class]

    if len(npc) > 1:
        modifier = 1 if (npc[0] == "#") else -1
        return {
            "text": repeat_text("^", "_", octave) + npc,
            "pitch_class": int(npc[1]),
            "octave": octave,
            "modifier": modifier,
        }

    return {
        "text": repeat_text("^", "_", octave) + npc,
        "pitch_class": int(npc),
        "octave": octave,
    }


def chord_from_degree(
    degree: int, name: str, scale: str, root: str | int, num_octaves: int = 1
) -> list[int]:
    """Generate chord from scale

    Args:
        degree (int): Chord degree
        name (str): Chord type
        scale (str): Scale name
        root (str | int): Root for the chord
        num_octaves (int, optional): Number of octaves. Defaults to 1.

    Returns:
        list[int]: Created chord as list of midi notes
    """
    root = note_name_to_midi(root) if isinstance(root, str) else root

    if (
        name is None
        and isinstance(scale, str)
        and scale.lower().capitalize() == "Chromatic"
    ):
        name = "major"

    if name:
        return named_chord_from_degree(degree, name, root, scale, num_octaves)
    else:
        return get_chord_from_scale(degree, root, scale)


def named_chord_from_degree(
    degree: int,
    name: str = "major",
    root: int = 60,
    scale: str = "Major",
    num_octaves: int = 1,
) -> list[int]:
    """Generates chord from given roman numeral and chord name

    Args:
        roman (str): Roman numeral
        name (str, optional): Chord name. Defaults to "major".
        num_octaves (int, optional): Number of octaves for the chord. Defaults to 1.

    Returns:
        list[int]: _description_
    """
    intervals = CHORDS.get(name, CHORDS["major"])
    scale_degree = get_scale_notes(scale, root)[degree - 1]
    notes = []
    for cur_oct in range(num_octaves):
        for interval in intervals:
            notes.append(scale_degree + interval + (cur_oct * 12))
    return notes


def resolve_pitch_bend(note_value: float, semitones: int = 1) -> int:
    """Resolves pitch bend value from float midi note

    Args:
        note_value (float): Note value as float, eg. 60.41123
        semitones (int, optional): Number of semitones to scale the pitch bend. Defaults to 1.

    Returns:
        int: Returns pitch bend value ranging from 0 to 16383. 8192 means no bend.
    """
    midi_bend_value = 8192
    if isinstance(note_value, float) and note_value % 1 != 0.0:
        start_value = (
            note_value if note_value > round(note_value) else round(note_value)
        )
        end_value = round(note_value) if note_value > round(note_value) else note_value
        bend_diff = midi_to_freq(start_value) / midi_to_freq(end_value)
        bend_target = 1200 * log2(bend_diff)
        # https://www.cs.cmu.edu/~rbd/doc/cmt/part7.html
        midi_bend_value = 8192 + int(8191 * (bend_target / (100 * semitones)))
    return (note_value, midi_bend_value)


def cents_to_semitones(cents: list) -> tuple[float]:
    """Tranform cents to semitones"""
    if cents[0] != 0.0:
        cents = [0.0] + cents
    semitone_scale = []
    for i, cent in enumerate(cents[:-1]):
        semitone_interval = (cents[i + 1] - cent) / 100
        semitone_scale.append(semitone_interval)
    return tuple(semitone_scale)


def ratio_to_cents(ratio: float) -> float:
    """Transform ratio to cents"""
    return 1200.0 * log2(float(ratio))


def monzo_to_cents(monzo) -> float:
    """
    Convert a monzo to cents using the prime factorization method.

    Args:
        monzo (list): A list of integers representing the exponents of the prime factorization

    Returns:
        float: The value in cents
    """
    # Calculate the prime factors of the indices in the monzo
    max_index = len(monzo)
    primes = list(islice(gen_primes(), max_index + 1))

    # Product of the prime factors raised to the corresponding exponents
    ratio = 1
    for i in range(max_index):
        ratio *= primes[i] ** monzo[i]

    # Frequency ratio to cents
    cents = 1200 * log2(ratio)

    return cents
