""" Ziffers classes for the parsed notation """
from dataclasses import dataclass, field
import itertools
import operator
import random
from .defaults import DEFAULT_OPTIONS
from .scale import note_from_pc, midi_to_pitch_class


@dataclass
class Meta:
    """Abstract class for all Ziffers items"""

    def update(self, new_values):
        """Update attributes from dict"""
        for key, value in new_values.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def update_new(self, new_values):
        """Updates new attributes from dict"""
        for key, value in new_values.items():
            if hasattr(self, key):
                if getattr(self, key) is None:
                    setattr(self, key, value)


@dataclass
class Item(Meta):
    """Class for all Ziffers text based items"""

    text: str


@dataclass
class Whitespace(Item):
    """Class for whitespace"""

    item_type: str = field(default=None, repr=False, init=False)


@dataclass
class DurationChange(Item):
    """Class for changing duration"""

    value: float
    key: str = field(default="duration", repr=False, init=False)
    item_type: str = field(default="change", repr=False, init=False)


@dataclass
class OctaveChange(Item):
    """Class for changing octave"""

    value: int
    key: str = field(default="octave", repr=False, init=False)
    item_type: str = field(default="change", repr=False, init=False)


@dataclass
class OctaveAdd(Item):
    """Class for modifying octave"""

    value: int
    key: str = field(default="octave", repr=False, init=False)
    item_type: str = field(default="add", repr=False, init=False)


@dataclass
class Event(Item):
    """Abstract class for events with duration"""

    duration: float = field(default=None)


@dataclass
class Pitch(Event):
    """Class for pitch in time"""

    pitch_class: int = field(default=None)
    octave: int = field(default=None)
    modifier: int = field(default=None)
    note: int = field(default=None)

    def set_note(self, note: int):
        self.note = note
        return note


@dataclass
class RandomPitch(Event):
    """Class for random pitch"""

    pitch_class: int = field(default=None)


@dataclass
class RandomPercent(Item):
    """Class for random percent"""

    percent: float = field(default=None)


@dataclass
class Chord(Event):
    """Class for chords"""

    pitch_classes: list[Pitch] = field(default=None)
    notes: list[int] = field(default=None)

    def set_notes(self, notes: list[int]):
        """Set notes to the class"""
        self.notes = notes

@dataclass
class RomanNumeral(Event):
    """Class for roman numbers"""

    value: str = field(default=None)
    chord_type: str = field(default=None)
    notes: list[int] = field(default_factory=[])
    pitch_classes: list = None

    def set_notes(self, chord_notes: list[int]):
        self.notes = chord_notes

    def set_pitch_classes(self, pitches: list[tuple]):
        if self.pitch_classes == None:
            self.pitch_classes = []
        for pitch in pitches:
            self.pitch_classes.append(Pitch(**pitch))


@dataclass
class Function(Event):
    """Class for functions"""

    run: str = field(default=None)


@dataclass
class Sequence(Meta):
    """Class for sequences of items"""

    values: list[Item]
    text: str = field(default=None)
    wrap_start: str = field(default=None, repr=False)
    wrap_end: str = field(default=None, repr=False)
    local_index: int = field(default=0, init=False)

    def __post_init__(self):
        self.text = self.__collect_text()

    def __iter__(self):
        return self

    def __next__(self):
        if self.local_index < len(self.values):
            next_item = self.values[self.local_index]
            self.local_index += 1
            return next_item

        self.local_index = 0
        raise StopIteration

    def update_values(self, new_values):
        """Update value attributes from dict"""
        for key, value in new_values.items():
            for obj in self.values:
                if key != "text" and hasattr(obj, key):
                    setattr(obj, key, value)

    def __collect_text(self) -> str:
        """Collect text value from values"""
        text = "".join([val.text for val in self.values])
        if self.wrap_start is not None:
            text = self.wrap_start + text
        if self.wrap_end is not None:
            text = text + self.wrap_end
        return text

    def flatten_values(self):
        """Flattens the Ziffers object tree"""
        for item in self.values:
            if isinstance(item, Sequence):
                yield from item.flatten_values()
            else:
                yield item


@dataclass
class Ziffers(Sequence):
    """Main class for holding options and the current state"""

    options: dict = field(default_factory=DEFAULT_OPTIONS)
    loop_i: int = 0
    iterator: iter = field(default=None, repr=False)
    current: Whitespace | DurationChange | OctaveChange | OctaveAdd = field(
        default=None
    )

    def __post_init__(self):
        super().__post_init__()
        self.iterator = self.flatten_values()

    def __next__(self):
        self.current = next(self.iterator)

        # Skip whitespace and collect duration & octave changes
        while isinstance(
            self.current, (Whitespace, DurationChange, OctaveChange, OctaveAdd)
        ):
            if self.current.item_type == "change":  # Change options
                self.options[self.current.key] = self.current.value
            elif self.current.item_type == "add":
                if self.current.key in self.options:  # Add to existing value
                    self.options[self.current.key] += self.current.value
                else:  # Create value if not existing
                    self.options[self.current.key] = self.current.value

            self.current = next(self.iterator)  # Skip item

        # Update collected options & default options
        self.current.update_new(self.options)

        # Resolve note(s) from scale
        if set(("key", "scale")) <= self.options.keys():
            key = self.options["key"]
            scale = self.options["scale"]
            if isinstance(self.current, (Pitch, RandomPitch)):
                note = note_from_pc(key,self.current.pitch_class,scale)
                self.current.set_note(note)
            elif isinstance(self.current,Chord):
                pcs = self.current.pitch_classes
                notes = [pc.set_note(note_from_pc(key, pc.pitch_class, scale)) for pc in pcs]
                self.current.set_notes(notes)
            elif isinstance(self.current,RomanNumeral):
                pitch_classes = [midi_to_pitch_class(note, key, scale) for note in self.current.notes]
                self.current.set_pitch_classes(pitch_classes)


        self.loop_i += 1
        return self.current

    def take(self, num: int) -> list[Pitch]:
        """Take number of pitch classes from the parsed sequence. Cycles from the beginning.

        Args:
            num (int): Number of pitch classes to take from the sequence

        Returns:
            list: List of pitch class items
        """
        return list(itertools.islice(itertools.cycle(self), num))

    def loop(self) -> iter:
        return itertools.cycle(self.iterator)

    def set_defaults(self, options: dict):
        """Sets options for the parser

        Args:
            options (dict): Options as a dict
        """
        self.options = DEFAULT_OPTIONS | options

    # TODO: Refactor these
    def pitch_classes(self) -> list[int]:
        """Return list of pitch classes as ints"""
        return [val.pitch_class for val in self.values if isinstance(val, Pitch)]

    def durations(self) -> list[float]:
        """Return list of pitch durations as floats"""
        return [val.dur for val in self.values if isinstance(val, Pitch)]

    def pairs(self) -> list[tuple]:
        """Return list of pitches and durations"""
        return [
            (val.pitch_class, val.dur) for val in self.values if isinstance(val, Pitch)
        ]

    def octaves(self) -> list[int]:
        """Return list of octaves"""
        return [val.octave for val in self.values if isinstance(val, Pitch)]


@dataclass
class ListSequence(Sequence):
    """Class for Ziffers list sequences"""

    wrap_start: str = field(default="(", repr=False)
    wrap_end: str = field(default=")", repr=False)


@dataclass
class Integer(Item):
    """Class for integers"""

    value: int


@dataclass
class RandomInteger(Item):
    """Class for random integer"""

    min: int
    max: int

    def __post_init__(self):
        if self.min > self.max:
            new_max = self.min
            self.min = self.max
            self.max = new_max

    def value(self):
        """Evaluate the random value for the generator"""
        return random.randint(self.min, self.max)


@dataclass
class RepeatedListSequence(Sequence):
    """Class for Ziffers list sequences"""

    repeats: RandomInteger | Integer = field(default_factory=Integer(value=1, text="1"))
    wrap_start: str = field(default="(:", repr=False)
    wrap_end: str = field(default=":)", repr=False)


@dataclass
class Subdivision(Item):
    """Class for subdivisions"""

    values: list[Event]


@dataclass
class Cyclic(Sequence):
    """Class for cyclic sequences"""

    cycle: int = 0
    wrap_start: str = field(default="<", repr=False)
    wrap_end: str = field(default=">", repr=False)

    def __post_init__(self):
        super().__post_init__()
        # TODO: Do spaced need to be filtered out?
        self.values = [val for val in self.values if isinstance(val, Whitespace)]

    def value(self):
        """Get the value for the current cycle"""
        return self.values[self.cycle]

    def next_cycle(self, cycle: int):
        """Evaluate next cycle"""
        self.cycle = self.cycle + 1


@dataclass
class Range(Item):
    """Class for range"""

    start: int = field(default=None)
    end: int = field(default=None)


ops = {
    "+": operator.add,
    "-": operator.sub,
    "*": operator.mul,
    "/": operator.truediv,
    "%": operator.mod,
}


@dataclass
class Operator(Item):
    """Class for math operators"""

    value: ... = field(init=False, repr=False)

    def __post_init__(self):
        self.value = ops[self.text]


@dataclass
class ListOperation(Sequence):
    """Class for list operations"""

    def run(self):
        """Run operations"""
        pass


@dataclass
class Operation(Item):
    """Class for lisp-like operations: (+ 1 2 3) etc."""

    values: list
    operator: operator


@dataclass
class Eval(Sequence):
    """Class for evaluation notation"""

    result: ... = None
    wrap_start: str = field(default="{", repr=False)
    wrap_end: str = field(default="}", repr=False)

    def __post_init__(self):
        super().__post_init__()
        self.result = eval(self.text)


@dataclass
class Atom(Item):
    """Class for evaluable atoms"""

    value: ...


@dataclass
class Euclid(Item):
    """Class for euclidean cycles"""

    pulses: int
    length: int
    onset: list
    offset: list = field(default=None)
    rotate: int = field(default=None)


@dataclass
class RepeatedSequence(Sequence):
    """Class for repeats"""

    repeats: RandomInteger | Integer = field(default_factory=Integer(value=1, text="1"))
    wrap_start: str = field(default="[:", repr=False)
    wrap_end: str = field(default=":]", repr=False)
