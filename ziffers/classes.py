""" Ziffers classes for the parsed notation """
from dataclasses import dataclass, field, replace
import itertools
import operator
import random
from .defaults import DEFAULT_OPTIONS
from .scale import note_from_pc, midi_to_pitch_class


@dataclass(kw_only=True)
class Meta:
    """Abstract class for all Ziffers items"""

    kwargs: dict = field(default=None, repr=False)

    def __post_init__(self):
        if self.kwargs:
            for key, val in self.kwargs.items():
                setattr(self, key, val)

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


@dataclass(kw_only=True)
class Item(Meta):
    """Class for all Ziffers text based items"""

    text: str = field(default=None)

    def get_item(self):
        """Return the item"""
        return self


@dataclass(kw_only=True)
class Whitespace:
    """Class for whitespace"""

    text: str
    item_type: str = field(default=None, repr=False, init=False)

    def get_item(self):
        """Returns None. Used in filtering"""
        return None


@dataclass(kw_only=True)
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


@dataclass(kw_only=True)
class OctaveAdd(Item):
    """Class for modifying octave"""

    value: int
    key: str = field(default="octave", repr=False, init=False)
    item_type: str = field(default="add", repr=False, init=False)


@dataclass(kw_only=True)
class Event(Item):
    """Abstract class for events with duration"""

    duration: float = field(default=None)


@dataclass(kw_only=True)
class Pitch(Event):
    """Class for pitch in time"""

    pitch_class: int
    octave: int = field(default=None)
    modifier: int = field(default=0)
    note: int = field(default=None)
    key: str = field(default=None)
    scale: str | list = field(default=None)

    def __post_init__(self):
        super().__post_init__()
        if self.text is None:
            self.text = str(self.pitch_class)
            self.update_note()

    def update_note(self):
        """Update note if Key, Scale and Pitch-class is present"""
        if (
            (self.key is not None)
            and (self.scale is not None)
            and (self.pitch_class is not None)
            and (self.note is None)
        ):
            note = note_from_pc(
                root=self.key,
                pitch_class=self.pitch_class,
                intervals=self.scale,
                modifier=self.modifier if self.modifier is not None else 0,
                octave=self.octave if self.octave is not None else 0,
            )
            self.set_note(note)

    def set_note(self, note: int) -> int:
        """Sets a note for the pitch and returns the note.

        Args:
            note (int): Midi note

        Returns:
            int: Returns the saved note
        """
        self.note = note
        return note

    # pylint: disable=locally-disabled, unused-argument
    def get_value(self) -> int:
        """Returns the pitch class

        Returns:
            int: Integer value for the pitch
        """
        return self.pitch_class


@dataclass(kw_only=True)
class RandomPitch(Event):
    """Class for random pitch"""

    pitch_class: int = field(default=None)

    # pylint: disable=locally-disabled, unused-argument
    def get_value(self) -> int:
        """Return random value

        Returns:
            int: Returns random pitch
        """
        return self.pitch_class


@dataclass(kw_only=True)
class RandomPercent(Item):
    """Class for random percent"""

    percent: float = field(default=None)


@dataclass(kw_only=True)
class Chord(Event):
    """Class for chords"""

    pitch_classes: list[Pitch] = field(default=None)
    notes: list[int] = field(default=None)

    def set_notes(self, notes: list[int]):
        """Set notes to the class"""
        self.notes = notes


@dataclass(kw_only=True)
class RomanNumeral(Event):
    """Class for roman numbers"""

    value: str = field(default=None)
    chord_type: str = field(default=None)
    notes: list[int] = field(default_factory=[])
    pitch_classes: list = None

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


@dataclass(kw_only=True)
class Function(Event):
    """Class for functions"""

    run: str = field(default=None)


@dataclass(kw_only=True)
class Sequence(Meta):
    """Class for sequences of items"""

    values: list
    text: str = field(default=None)
    wrap_start: str = field(default=None, repr=False)
    wrap_end: str = field(default=None, repr=False)
    local_index: int = field(default=0, init=False)
    evaluation: bool = field(default=False, init=False)

    def __post_init__(self):
        super().__post_init__()
        self.text = self.__collect_text()

    def __getitem__(self, index):
        return self.values[index]

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

    def evaluate_tree(self, options=None):
        """Evaluates and flattens the Ziffers object tree"""
        for item in self.values:
            if isinstance(item, Sequence):
                if item.evaluation:
                    yield from item.evaluate(options)
                else:
                    yield from item.evaluate_tree(options)
            else:
                # Get value / generated value from the item
                current = item.get_item()
                # Ignore items that returns None
                if current is not None:
                    if isinstance(current, (DurationChange, OctaveChange, OctaveAdd)):
                        options = self.__update_options(current, options)
                    else:
                        if set(("key", "scale")) <= options.keys():
                            if isinstance(current, Cyclic):
                                current = current.get_value()
                            if isinstance(current, (Pitch, RandomPitch, RandomInteger)):
                                current = self.__update_pitch(current, options)
                            elif isinstance(current, Chord):
                                current = self.__update_chord(current, options)
                            elif isinstance(current, RomanNumeral):
                                current = self.__create_chord_from_roman(
                                    current, options
                                )
                        current.update_new(options)
                        yield current

    def filter(self, keep: tuple):
        """Filter out items from sequence.

        Args:
            keep (tuple): Tuple describing classes to keep

        Returns:
            Sequence: Copy of the sequence with filtered values.
        """
        return replace(
            self, values=[item for item in self.values if isinstance(item, keep)]
        )

    def __update_options(self, current: Item, options: dict) -> dict:
        """Update options based on current item

        Args:
            current (Item): Current item like Duration change, Octave change etc.
            options (dict): Current options

        Returns:
            dict: Updated options
        """
        if current.item_type == "change":  # Change options
            options[current.key] = current.value
        elif current.item_type == "add":
            if current.key in options:  # Add to existing value
                options[current.key] += current.value
            else:  # Create value if not existing
                options[current.key] = current.value
        return options

    def __update_pitch(self, current: Item, options: dict) -> dict:
        """Update pich based on optons

        Args:
            current (Item): _description_
            options (dict): _description_

        Returns:
            dict: _description_
        """
        if hasattr(current, "modifier"):
            c_modifier = 0
        elif "modifier" in options:
            c_modifier = options["modifier"]
        else:
            c_modifier = 0

        if hasattr(current, "octave"):
            c_octave = 0
        elif "octave" in options:
            c_octave = options["octave"]
        else:
            c_octave = 0

        note = note_from_pc(
            root=options["key"],
            pitch_class=current.get_value(),
            intervals=options["scale"],
            modifier=c_modifier,
            octave=c_octave,
        )
        new_pitch = Pitch(
            pitch_class=current.get_value(),
            text=str(current.get_value()),
            note=note,
            octave=c_octave,
            modifier=c_modifier,
            kwargs=options,
        )
        return new_pitch

    def __update_chord(self, current: Chord, options: dict) -> Chord:
        """Update chord based on options

        Args:
            current (Chord): Current chord object
            options (dict): Options
            re (bool, optional): Re-evaluation flag. Defaults to False.

        Returns:
            Chord: Returns updated chord
        """
        pcs = current.pitch_classes
        notes = [
            pc.set_note(note_from_pc(options["key"], pc.pitch_class, options["scale"]))
            for pc in pcs
        ]
        current.set_notes(notes)
        return current

    def __create_chord_from_roman(self, current: RomanNumeral, options: dict) -> Chord:
        """Create chord fom roman numeral

        Args:
            current (RomanNumeral): Current roman numeral
            options (dict): Options
            re (bool, optional): Re-evaluation flag. Defaults to False.

        Returns:
            Chord: New chord created from Roman numeral
        """
        key = options["key"]
        scale = options["scale"]
        pitches = [midi_to_pitch_class(note, key, scale) for note in current.notes]
        chord_notes = [
            note_from_pc(
                root=key,
                pitch_class=pitch,
                intervals=scale,
                modifier=current.modifier if hasattr(current, "modifier") else 0,
            )
            for pitch in pitches
        ]
        chord = Chord(text="".join(pitches), pitch_classes=pitches, notes=chord_notes)
        return chord


@dataclass(kw_only=True)
class Ziffers(Sequence):
    """Main class for holding options and the current state"""

    options: dict = field(default_factory=DEFAULT_OPTIONS)
    loop_i: int = 0
    iterator = None
    current: Item = field(default=None)

    def __iter__(self):
        return self

    def __next__(self):
        self.current = next(self.iterator)
        self.loop_i += 1
        return self.current

    # pylint: disable=locally-disabled, dangerous-default-value
    def init_opts(self, options=None):
        """Evaluate the Ziffers tree using the options"""
        self.options.update(DEFAULT_OPTIONS)
        if options:
            self.options.update(options)
        else:
            self.options = DEFAULT_OPTIONS

        self.iterator = iter(self.evaluate_tree(self.options))

    def re_eval(self, options=None):
        """Re-evaluate the iterator"""
        self.options.update(DEFAULT_OPTIONS)
        if options:
            self.options.update(options)
        self.iterator = iter(self.evaluate_tree(self.options))

    def get_list(self):
        """Return list"""
        return list(self)

    def take(self, num: int) -> list[Pitch]:
        """Take number of pitch classes from the parsed sequence. Cycles from the beginning.

        Args:
            num (int): Number of pitch classes to take from the sequence

        Returns:
            list: List of pitch class items
        """
        return list(itertools.islice(itertools.cycle(self), num))

    def loop(self) -> iter:
        """Return cyclic loop"""
        return itertools.cycle(iter(self))

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


@dataclass(kw_only=True)
class ListSequence(Sequence):
    """Class for Ziffers list sequences"""

    wrap_start: str = field(default="(", repr=False)
    wrap_end: str = field(default=")", repr=False)


@dataclass(kw_only=True)
class Integer(Item):
    """Class for integers"""

    value: int

    # pylint: disable=locally-disabled, unused-argument
    def get_value(self):
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
    def get_value(self):
        """Evaluate the random value for the generator"""
        return random.randint(self.min, self.max)


@dataclass(kw_only=True)
class RepeatedListSequence(Sequence):
    """Class for Ziffers list sequences"""

    repeats: RandomInteger | Integer = field(default_factory=Integer(value=1, text="1"))
    wrap_start: str = field(default="(:", repr=False)
    wrap_end: str = field(default=":)", repr=False)


@dataclass(kw_only=True)
class Subdivision(Item):
    """Class for subdivisions"""

    values: list[Event]


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

    def get_value(self):
        """Get the value for the current cycle"""
        value = self.values[self.cycle % len(self.values)]
        self.cycle += 1
        return value


@dataclass(kw_only=True)
class Range(Item):
    """Class for range"""

    start: int = field(default=None)
    end: int = field(default=None)


@dataclass(kw_only=True)
class Operator(Item):
    """Class for math operators"""

    value: ...


@dataclass(kw_only=True)
class ListOperation(Sequence):
    """Class for list operations"""

    def __post_init__(self):
        super().__post_init__()
        self.evaluation = True

    def filter_operation(self, values):
        """Filtering for the operation elements"""
        keep = (Sequence, Event, RandomInteger, Integer, Cyclic)
        for item in values:
            if isinstance(item, Sequence):
                yield item.filter(keep)
            elif isinstance(item, keep):
                yield item

    def evaluate(self, options: dict):
        """Evaluates the operation"""
        operators = self.values[1::2]  # Fetch every second operator element
        values = self.values[::2]  # Fetch every second list element
        values = list(self.filter_operation(values))  # Filter out crap
        result = values[0]  # Start results with the first array
        for i, operand in enumerate(operators):
            operation = operand.value
            right_value = values[i + 1]
            if isinstance(right_value, Sequence):
                result = [
                    Pitch(
                        pitch_class=operation(x.get_value(), y.get_value()),
                        kwargs=options,
                    )
                    for x in result
                    for y in right_value
                ]
            else:
                result = [
                    Pitch(
                        pitch_class=operation(x.get_value(), right_value.get_value()),
                        kwargs=options,
                    )
                    for x in result
                ]
        return Sequence(values=result)


@dataclass(kw_only=True)
class Operation(Item):
    """Class for lisp-like operations: (+ 1 2 3) etc."""

    values: list
    operator: operator


@dataclass(kw_only=True)
class Eval(Sequence):
    """Class for evaluation notation"""

    result: ... = None
    wrap_start: str = field(default="{", repr=False)
    wrap_end: str = field(default="}", repr=False)

    def __post_init__(self):
        super().__post_init__()
        self.result = eval(self.text)


@dataclass(kw_only=True)
class Atom(Item):
    """Class for evaluable atoms"""

    value: ...


@dataclass(kw_only=True)
class Euclid(Item):
    """Class for euclidean cycles"""

    pulses: int
    length: int
    onset: list
    offset: list = field(default=None)
    rotate: int = field(default=None)


@dataclass(kw_only=True)
class RepeatedSequence(Sequence):
    """Class for repeats"""

    repeats: RandomInteger | Integer = field(default_factory=Integer(value=1, text="1"))
    wrap_start: str = field(default="[:", repr=False)
    wrap_end: str = field(default=":]", repr=False)
