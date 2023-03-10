""" Ziffers item classes """
from dataclasses import dataclass, field, asdict
from math import floor
import operator
import random
from ..scale import (
    note_from_pc,
    midi_to_pitch_class,
    midi_to_freq,
    get_scale_length,
    chord_from_degree,
)
from ..common import repeat_text


@dataclass(kw_only=True)
class Meta:
    """Abstract class for all Ziffers items"""

    kwargs: dict = field(default=None, repr=False)
    local_options: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.kwargs:
            self.update_options(self.kwargs)

    def replace_options(self, new_values):
        """Replaces attribute values from dict"""
        for key, value in new_values.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def update_options(self, options):
        """Updates attribute values only if value is None"""
        merged_options = self.local_options | options
        for key, value in merged_options.items():
            if hasattr(self, key):
                if key == "octave":
                    local_value = self.local_options.get("octave", False)
                    oct_change = self.local_options.get("octave_change", False)
                    if oct_change:
                        setattr(self, key, oct_change)
                    elif local_value:
                        setattr(self, key, value + local_value)
                    elif getattr(self, key) is None:
                        setattr(self, key, value)
                elif getattr(self, key) is None:
                    local_value = self.local_options.get(key, False)
                    if local_value:
                        value = local_value
                    setattr(self, key, value)
                    if key == "duration":
                        setattr(self, "beat", value * 4)

    def dict(self):
        """Returns safe dict from the dataclass"""
        return {k: str(v) for k, v in asdict(self).items()}


@dataclass(kw_only=True)
class Item(Meta):
    """Class for all Ziffers text based items"""

    text: str = field(default=None)
    measure: int = field(default=0, init=False)

    def get_updated_item(self, options: dict):
        """Get updated item with replaced options

        Args:
            options (dict): Options as a dict

        Returns:
            Item: Returns updated item
        """
        self.replace_options(options)
        return self

    def get_options(self) -> dict:
        """Return local options from item

        Returns:
            dict: Options as a dict
        """
        keys = ["octave", "modifier", "key", "scale", "duration"]
        return {key: getattr(self, key) for key in keys if hasattr(self, key)}


@dataclass(kw_only=True)
class Whitespace:
    """Class for whitespace"""

    text: str


@dataclass(kw_only=True)
class Modification(Item):
    """Superclass for pitch modifications"""

    key: str
    value: ...

    def as_options(self):
        """Return modification as a dict"""
        return {self.key: self.value}


@dataclass(kw_only=True)
class DurationChange(Modification):
    """Class for changing duration"""

    value: float
    key: str = field(default="duration", repr=False, init=False)


@dataclass
class OctaveChange(Modification):
    """Class for changing octave"""

    value: int
    key: str = field(default="octave", repr=False, init=False)


@dataclass(kw_only=True)
class OctaveAdd(Modification):
    """Class for modifying octave"""

    value: int
    key: str = field(default="octave", repr=False, init=False)


@dataclass(kw_only=True)
class Event(Item):
    """Abstract class for events with duration"""

    duration: float = field(default=None)
    beat: float = field(default=None)

    def get_duration(self):
        """Getter for duration"""
        return self.duration

    def get_beat(self):
        """Getter for beat"""
        return self.beat


@dataclass
class Rest(Event):
    """Class for rests"""


@dataclass
class Measure(Item):
    """Class for measures/bars. Used to reset default options."""

    text: str = field(default="|", init=False)

    def reset_options(self, options: dict):
        """Reset options when measure changes"""
        next_measure = options.get("measure", 0) + 1
        start_options = options["start_options"].copy()
        options.clear()
        options.update(start_options)
        options["measure"] = next_measure
        options["start_options"] = start_options.copy()
        self.measure = next_measure


@dataclass(kw_only=True)
class Pitch(Event):
    """Class for pitch in time"""

    pitch_class: int
    pitch_bend: float = field(default=None)
    octave: int = field(default=None)
    modifier: int = field(default=None)
    note: int = field(default=None)
    key: str = field(default=None)
    scale: str | list = field(default=None)
    freq: float = field(default=None)

    def __post_init__(self):
        super().__post_init__()
        if self.text is None:
            self.text = str(self.pitch_class)
            self.update_note()
            # self._update_text()

    def _update_text(self):
        if self.octave is not None:
            self.text = repeat_text("^", "_", self.octave) + self.text
        if self.modifier is not None:
            self.text = repeat_text("#", "b", self.modifier) + self.text

    def get_note(self):
        """Getter for note"""
        return self.note

    def get_freq(self):
        """Getter for freq"""
        return self.freq

    def get_octave(self):
        """Getter for octave"""
        return self.octave

    def get_pitch_class(self):
        """Getter for pitche"""
        return self.pitch_class
    
    def get_pitch_bend(self):
        """Getter for pitche"""
        return self.pitch_bend

    def update_note(self, force: bool = False):
        """Update note if Key, Scale and Pitch-class are present"""
        if (
            (self.key is not None)
            and (self.scale is not None)
            and (self.pitch_class is not None)
            and (self.note is None or force)
        ):
            note, pitch_bend = note_from_pc(
                root=self.key,
                pitch_class=self.pitch_class,
                intervals=self.scale,
                modifier=self.modifier if self.modifier is not None else 0,
                octave=self.octave if self.octave is not None else 0,
            )
            self.pitch_bend = pitch_bend
            self.freq = midi_to_freq(note)
            self.note = floor(note)
        if self.duration is not None:
            self.beat = self.duration * 4

    def check_note(self, options: dict):
        """Check for note modification"""
        if "key" in options and self.key is not options["key"]:
            self.key = options["key"]
            edit = True
        if "scale" in options and self.scale is not options["scale"]:
            self.scale = options["scale"]
            edit = True
        if edit:
            self.update_note(True)

    def set_note(self, note: int) -> int:
        """Sets a note for the pitch and returns the note.

        Args:
            note (int): Midi note

        Returns:
            int: Returns the saved note
        """
        self.note = note
        return note

    def set_freq(self, freq: float):
        """Set frequency for the pitch object"""
        self.freq = freq

    # pylint: disable=locally-disabled, unused-argument
    def get_value(self, options) -> int:
        """Returns the pitch class

        Returns:
            int: Integer value for the pitch
        """
        return self.pitch_class


@dataclass(kw_only=True)
class RandomPitch(Event):
    """Class for random pitch"""

    pitch_class: int = field(default=None)

    def get_value(self, options: dict) -> int:
        """Return random value

        Returns:
            int: Returns random pitch
        """
        return random.randint(
            0, get_scale_length(options.get("scale", "Major")) if options else 9
        )


@dataclass(kw_only=True)
class RandomPercent(Item):
    """Class for random percent"""

    percent: float = field(default=None)


@dataclass(kw_only=True)
class Chord(Event):
    """Class for chords"""

    pitch_classes: list[Pitch] = field(default=None)
    notes: list[int] = field(default=None)
    inversions: int = field(default=None)
    pitches: list[int] = field(default=None, init=False)
    pitch_bends: list[int] = field(default=None, init=False)
    freqs: list[float] = field(default=None, init=False)
    octaves: list[int] = field(default=None, init=False)
    durations: list[float] = field(default=None, init=False)
    beats: list[float] = field(default=None, init=False)

    def __post_init__(self):
        if self.inversions is not None:
            self.invert(self.inversions)

    @property
    def note(self):
        """Synonym for notes"""
        return self.notes

    def set_notes(self, notes: list[int]):
        """Set notes to the class"""
        self.notes = notes

    def get_note(self):
        """Getter for  notes"""
        return self.notes

    def get_freq(self):
        """Getter for  freqs"""
        return self.freqs

    def get_octave(self):
        """Getter for  octaves"""
        return self.octaves

    def get_beat(self):
        """Getter for  beats"""
        return self.beats

    def get_pitch_class(self):
        """Getter for  pitches"""
        return self.pitches
    
    def get_pitch_bend(self):
        """Getter for pitche"""
        return self.pitch_bends

    def get_duration(self):
        """Getter for  durations"""
        return self.durations

    def invert(self, value: int):
        """Chord inversion"""
        new_pitches = (
            list(reversed(self.pitch_classes)) if value < 0 else self.pitch_classes
        )
        for _ in range(abs(value)):
            new_pitch = new_pitches[_ % len(new_pitches)]
            if not new_pitch.local_options.get("octave"):
                new_pitch.local_options["octave"] = 0
            new_pitch.local_options["octave"] += -1 if value <= 0 else 1

        self.pitch_classes = new_pitches

    def update_notes(self, options=None):
        """Update notes"""
        pitches, pitch_bends, notes, freqs, octaves, durations, beats = ([] for _ in range(7))

        # Update notes
        for pitch in self.pitch_classes:
            if options is not None:
                pitch.update_options(options)
            pitch.update_note(True)

        # Sort by generated notes
        self.pitch_classes = sorted(self.pitch_classes, key=lambda x: x.note)

        # Create helper lists
        for pitch in self.pitch_classes:
            pitches.append(pitch.pitch_class)
            pitch_bends.append(pitch.pitch_bend)
            notes.append(pitch.note)
            freqs.append(pitch.freq)
            octaves.append(pitch.octave)
            durations.append(pitch.duration)
            beats.append(pitch.beat)

        self.pitches = pitches
        self.pitch_bends = pitch_bends
        self.notes = notes
        self.freqs = freqs
        self.octaves = octaves
        self.durations = durations
        self.duration = durations[0]
        self.beats = beats
        self.text = "".join([val.text for val in self.pitch_classes])


@dataclass(kw_only=True)
class RomanNumeral(Event):
    """Class for roman numbers"""

    value: str = field(default=None)
    chord_type: str = field(default=None)
    notes: list[int] = field(default=None, init=False)
    pitch_classes: list = field(default=None, init=False)
    inversions: int = field(default=None)
    evaluated_chord: Chord = None

    def set_notes(self, chord_notes: list[int]):
        """Set notes to roman numeral

        Args:
            chord_notes (list[int]): List of notes in midi to be added
        """
        self.notes = chord_notes

    def set_pitch_classes(self, pitches: list[tuple]):
        """Set pitch classes to roman numeral

        Args:
            pitches (list[tuple]): Pitch classes to be added
        """
        if self.pitch_classes is None:
            self.pitch_classes = []
        for pitch in pitches:
            self.pitch_classes.append(Pitch(**pitch))

    def evaluate_chord(self, options: dict) -> Chord:
        """Create chord fom roman numeral"""
        key = options["key"]
        scale = options["scale"]
        pitch_text = ""
        pitch_classes = []
        self.notes = chord_from_degree(
            self.value, self.chord_type, options["scale"], options["key"]
        )
        for note in self.notes:
            pitch_dict = midi_to_pitch_class(note, key, scale)
            pitch_classes.append(
                Pitch(
                    pitch_class=pitch_dict["pitch_class"],
                    note=note,
                    freq=midi_to_freq(note),
                    kwargs=(options | pitch_dict),
                )
            )
            pitch_text += pitch_dict["text"]

        chord = Chord(
            text=pitch_text,
            pitch_classes=pitch_classes,
            duration=options["duration"],
            notes=self.notes,
            kwargs=options,
            inversions=self.inversions,
        )

        chord.update_notes(options)

        self.evaluated_chord = chord

        return chord


@dataclass(kw_only=True)
class Function(Event):
    """Class for functions"""

    run: ... = field(default=None)


@dataclass(kw_only=True)
class FunctionList(Event):
    """Class for functions"""

    values: list


@dataclass(kw_only=True)
class VariableAssignment(Item):
    """Class for defining variables"""

    variable: str
    value: Item
    pre_eval: bool


@dataclass(kw_only=True)
class Variable(Event):
    """Class for using variables"""

    name: str


@dataclass(kw_only=True)
class Sample(Event):
    """Class for samples"""

    name: str


@dataclass(kw_only=True)
class VariableList(Item):
    """Class for using variables"""

    values: list


@dataclass(kw_only=True)
class Integer(Item):
    """Class for integers"""

    value: int

    # pylint: disable=locally-disabled, unused-argument
    def get_value(self, options):
        """Return value of the integer"""
        return self.value


@dataclass(kw_only=True)
class RandomInteger(Item):
    """Class for random integer"""

    min: int
    max: int

    def __post_init__(self):
        super().__post_init__()
        if self.min > self.max:
            new_max = self.min
            self.min = self.max
            self.max = new_max

    # pylint: disable=locally-disabled, unused-argument
    def get_value(self, options: dict = None):
        """Evaluate the random value for the generator"""
        return random.randint(self.min, self.max)


@dataclass(kw_only=True)
class Cyclic(Item):
    """Class for cyclic sequences"""

    values: list
    cycle: int = 0
    wrap_start: str = field(default="<", repr=False)
    wrap_end: str = field(default=">", repr=False)

    def __post_init__(self):
        super().__post_init__()
        self.text = self.__collect_text()
        self.values = [val for val in self.values if not isinstance(val, Whitespace)]

    def __collect_text(self) -> str:
        """Collect text value from values"""
        text = "".join([val.text for val in self.values])
        if self.wrap_start is not None:
            text = self.wrap_start + text
        if self.wrap_end is not None:
            text = text + self.wrap_end
        return text

    def get_value(self, options=None):
        """Get the value for the current cycle"""
        value = self.values[self.cycle % len(self.values)]
        self.cycle += 1
        return value


@dataclass(kw_only=True)
class Range(Item):
    """Class for range"""

    start: int = field(default=None)
    end: int = field(default=None)

    def evaluate(self, options):
        """Evaluates range and generates a generator of Pitches"""
        merged_options = options | self.local_options
        if options["octave"]:
            merged_options["octave"] += options["octave"]
        if self.start < self.end:
            for i in range(self.start, self.end + 1):
                yield Pitch(pitch_class=i, kwargs=merged_options)
        elif self.start > self.end:
            for i in reversed(range(self.end, self.start + 1)):
                yield Pitch(pitch_class=i, kwargs=merged_options)
        else:
            yield Pitch(pitch_class=self.start, kwargs=merged_options)


@dataclass(kw_only=True)
class Operator(Item):
    """Class for math operators"""

    value: ...


@dataclass(kw_only=True)
class Operation(Item):
    """Class for lisp-like operations: (+ 1 2 3) etc."""

    values: list
    operator: operator


@dataclass(kw_only=True)
class Atom(Item):
    """Class for evaluable atoms"""

    value: ...
