""" Ziffers classes for the parsed notation """
from dataclasses import dataclass, field, replace, asdict
from itertools import product, islice, cycle
import operator
import random
from .defaults import DEFAULT_OPTIONS
from .scale import note_from_pc, midi_to_pitch_class, midi_to_freq, get_scale_length
from .common import euclidian_rhythm


@dataclass(kw_only=True)
class Meta:
    """Abstract class for all Ziffers items"""

    kwargs: dict = field(default=None, repr=False)

    def __post_init__(self):
        if self.kwargs:
            self.update_options(self.kwargs)

    def replace_options(self, new_values):
        """Replaces attribute values from dict"""
        for key, value in new_values.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def update_options(self, new_values):
        """Updates attribute values only if value is None"""
        for key, value in new_values.items():
            if hasattr(self, key):
                if getattr(self, key) is None:
                    setattr(self, key, value)

    def dict(self):
        """Returns safe dict from the dataclass"""
        return {k: str(v) for k, v in asdict(self).items()}


@dataclass(kw_only=True)
class Item(Meta):
    """Class for all Ziffers text based items"""

    text: str = field(default=None)

    def get_updated_item(self, options: dict):
        """Get updated item with replaced options

        Args:
            options (dict): Options as a dict

        Returns:
            Item: Returns updated item
        """
        self.replace_options(options)
        return self


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


@dataclass
class Rest(Event):
    """Class for rests"""


@dataclass(kw_only=True)
class Pitch(Event):
    """Class for pitch in time"""

    pitch_class: int
    octave: int = field(default=None)
    modifier: int = field(default=0)
    note: int = field(default=None)
    key: str = field(default=None)
    scale: str | list = field(default=None)
    freq: float = field(default=None)

    def __post_init__(self):
        super().__post_init__()
        if self.text is None:
            self.text = str(self.pitch_class)
        self.update_note()

    def update_note(self, force: bool = False):
        """Update note if Key, Scale and Pitch-class are present"""
        if (
            (self.key is not None)
            and (self.scale is not None)
            and (self.pitch_class is not None)
            and (self.note is None or force)
        ):
            note = note_from_pc(
                root=self.key,
                pitch_class=self.pitch_class,
                intervals=self.scale,
                modifier=self.modifier if self.modifier is not None else 0,
                octave=self.octave if self.octave is not None else 0,
            )
            self.freq = midi_to_freq(note)
            self.note = note

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
    freqs: list[float] = field(default=None, init=False)

    def set_notes(self, notes: list[int]):
        """Set notes to the class"""
        self.notes = notes

    def update_notes(self, options):
        """Update notes"""
        notes = []
        freqs = []

        for pitch in self.pitch_classes:
            pitch.update_options(options)
            pitch.update_note()
            notes.append(pitch.note)
            freqs.append(pitch.freq)

        self.notes = notes
        self.freqs = freqs


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
    evaluated_values: list = field(default=None)

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

    def evaluate_tree(self, options: dict = None, eval_tree: bool = False):
        """Evaluate the tree and return array of resolved pitches

        Args:
            options (dict, optional): Options for the pitches. Defaults to None.
            eval_tree (bool, optional): Flag for using the evaluated subtree. Defaults to False.
        """

        def _resolve_item(item: Meta, options: dict):
            """Resolve cyclic value"""
            if isinstance(item, Sequence):
                if isinstance(item, ListOperation):
                    yield from item.evaluate(options)
                elif isinstance(item, RepeatedSequence):
                    repeats = item.repeats.get_value(options)
                    yield from _normal_repeat(item.evaluated_values, repeats, options)
                elif isinstance(item, RepeatedListSequence):
                    repeats = item.repeats.get_value(options)
                    yield from _generative_repeat(item, repeats, options)
                elif isinstance(item, Subdivision):
                    item.evaluated_values = list(item.evaluate_tree(options))
                    yield item
                else:
                    yield from item.evaluate_tree(options)
            elif isinstance(item, Cyclic):
                yield from _resolve_item(item.get_value(), options)
            elif isinstance(item, Euclid):
                yield from _euclidean_items(item, options)
            elif isinstance(item, Modification):
                options = _update_options(item, options)
            elif isinstance(item, Meta):  # Filters whitespace
                yield _update_item(item, options)

        def _update_item(item, options):
            """Update or create new pitch"""
            if set(("key", "scale")) <= options.keys():
                if isinstance(item, Pitch):
                    item.update_options(options)
                    item.update_note()
                if isinstance(item, Rest):
                    item.update_options(options)
                elif isinstance(item, (RandomPitch, RandomInteger)):
                    item = _create_pitch(item, options)
                elif isinstance(item, Chord):
                    item.update_options(options)
                    item.update_notes(options)
                elif isinstance(item, RomanNumeral):
                    item = _create_chord_from_roman(item, options)
            return item

        # pylint: disable=locally-disabled, unused-variable
        def _generative_repeat(tree: list, times: int, options: dict):
            """Repeats items and generates new random values"""
            for i in range(times):
                for item in tree.evaluate_tree(options):
                    yield from _resolve_item(item, options)

        # pylint: disable=locally-disabled, unused-variable
        def _normal_repeat(tree: list, times: int, options: dict):
            """Repeats items with the same random values"""
            for i in range(times):
                for item in tree:
                    yield from _resolve_item(item, options)

        def _euclidean_items(euclid: Item, options: dict):
            """Loops values from generated euclidean sequence"""
            euclid.evaluate(options)
            for item in euclid.evaluated_values:
                yield from _resolve_item(item, options)

        def _loop_items(items, options):
            for item in items:
                yield from _resolve_item(item, options)

        def _update_options(current: Item, options: dict) -> dict:
            """Update options based on current item"""
            if isinstance(current, (OctaveChange, DurationChange)):
                options[current.key] = current.value
            elif isinstance(current, OctaveAdd):
                if current.key in options:  # Add to existing value
                    options[current.key] += current.value
                else:  # Create value if not existing
                    options[current.key] = current.value
            return options

        def _create_pitch(current: Item, options: dict) -> dict:
            """Create pitch based on values and options"""

            if "modifier" in options:
                c_modifier = options["modifier"]
            else:
                c_modifier = 0

            if hasattr(current, "modifier") and current.modifier is not None:
                c_modifier += current.modifier

            if "octave" in options:
                c_octave = options["octave"]
            else:
                c_octave = 0

            if hasattr(current, "octave") and current.octave is not None:
                c_octave += current.octave
            current_value = current.get_value(options)
            note = note_from_pc(
                root=options["key"],
                pitch_class=current_value,
                intervals=options["scale"],
                modifier=c_modifier,
                octave=c_octave,
            )
            new_pitch = Pitch(
                pitch_class=current_value,
                text=str(current_value),
                note=note,
                freq=midi_to_freq(note),
                octave=c_octave,
                modifier=c_modifier,
                kwargs=options,
            )
            return new_pitch

        def _create_chord_from_roman(current: RomanNumeral, options: dict) -> Chord:
            """Create chord fom roman numeral"""
            key = options["key"]
            scale = options["scale"]
            pitch_text = ""
            pitch_classes = []
            chord_notes = []
            for note in current.notes:
                pitch_dict = midi_to_pitch_class(note, key, scale)
                pitch_classes.append(
                    Pitch(
                        pitch_class=pitch_dict["pitch_class"],
                        kwargs=(pitch_dict | options),
                    )
                )
                pitch_text += pitch_dict["text"]
                chord_notes.append(
                    note_from_pc(
                        root=key,
                        pitch_class=pitch_dict["pitch_class"],
                        intervals=scale,
                        modifier=pitch_dict.get("modifier", 0),
                        octave=pitch_dict.get("octave", 0),
                    )
                )

            chord = Chord(
                text=pitch_text,
                pitch_classes=pitch_classes,
                notes=chord_notes,
                kwargs=options,
            )
            return chord

        # Start of the main function: Evaluate and flatten the Ziffers object tree
        values = self.evaluated_values if eval_tree else self.values
        for item in values:
            yield from _resolve_item(item, options)

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


@dataclass(kw_only=True)
class Ziffers(Sequence):
    """Main class for holding options and the current state"""

    options: dict = field(default_factory=DEFAULT_OPTIONS)
    start_options: dict = None
    loop_i: int = 0
    iterator = None
    current: Item = field(default=None)

    def __getitem__(self, index):
        return self.evaluated_values[index % len(self.evaluated_values)]

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

        self.start_options = self.options.copy()
        self.init_tree(self.options)

    def re_eval(self, options=None):
        """Re-evaluate the iterator"""
        self.options = self.start_options.copy()
        if options:
            self.options.update(options)
        self.init_tree(self.options)

    def init_tree(self, options):
        self.evaluated_values = list(self.evaluate_tree(options))
        self.evaluated_values = list(self.post_check())
        self.iterator = iter(self.evaluated_values)

    def post_check(self):
        for item in self.evaluated_values:
            if isinstance(item, Subdivision):
                yield from item.evaluate_durations()
            else:
                yield item

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
        return list(islice(cycle(self), num))

    def loop(self) -> iter:
        """Return cyclic loop"""
        return cycle(iter(self))

    def set_defaults(self, options: dict):
        """Sets options for the parser

        Args:
            options (dict): Options as a dict
        """
        self.options = DEFAULT_OPTIONS | options

    def pitch_classes(self) -> list[int]:
        """Return list of pitch classes as ints"""
        return [
            val.pitch_class for val in self.evaluated_values if isinstance(val, Pitch)
        ]

    def notes(self) -> list[int]:
        """Return list of midi notes"""
        return [val.note for val in self.evaluated_values if isinstance(val, Pitch)]

    def durations(self) -> list[float]:
        """Return list of pitch durations as floats"""
        return [val.duration for val in self.evaluated_values if isinstance(val, Event)]

    def pairs(self) -> list[tuple]:
        """Return list of pitches and durations"""
        return [
            (val.pitch_class, val.duration)
            for val in self.evaluated_values
            if isinstance(val, Pitch)
        ]

    def octaves(self) -> list[int]:
        """Return list of octaves"""
        return [val.octave for val in self.evaluated_values if isinstance(val, Pitch)]


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
class RepeatedListSequence(Sequence):
    """Class for Ziffers list sequences"""

    repeats: RandomInteger | Integer = field(default_factory=Integer(value=1, text="1"))
    wrap_start: str = field(default="(:", repr=False)
    wrap_end: str = field(default=":)", repr=False)


@dataclass(kw_only=True)
class Subdivision(Sequence):
    """Class for subdivisions"""

    def evaluate_durations(self, duration=None):
        """Calculate new durations by dividing with the number of items in the sequence"""
        if duration is None:
            duration = self.evaluated_values[0].duration
        new_d = duration / len(self.evaluated_values)
        for item in self.evaluated_values:
            if isinstance(item, Subdivision):
                yield from item.evaluate_durations(new_d)
            if isinstance(item, Event):
                if duration is not None:
                    item.duration = new_d
                yield item


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

    evaluated_values: list = None

    def __post_init__(self):
        super().__post_init__()
        self.evaluated_values = self.evaluate()

    # pylint: disable=locally-disabled, dangerous-default-value
    def evaluate(self, options=DEFAULT_OPTIONS):
        """Evaluates the operation"""

        def filter_operation(input_list):
            flattened_list = []

            for item in input_list:
                if isinstance(item, (list, Sequence)):
                    if isinstance(item, ListOperation):
                        flattened_list.extend(item.evaluated_values)
                    else:
                        flattened_list.append(filter_operation(item))
                elif isinstance(item, (Event, RandomInteger, Integer, Cyclic)):
                    flattened_list.append(item)

            if isinstance(input_list, Sequence):
                return replace(input_list, values=flattened_list)

            return flattened_list

        operators = self.values[1::2]  # Fetch every second operator element
        values = self.values[::2]  # Fetch every second list element
        values = filter_operation(values)  # Filter out crap
        left = values[0]  # Start results with the first array

        for i, operand in enumerate(operators):
            operation = operand.value
            right = values[i + 1]
            pairs = product(
                (right.values if isinstance(right, Sequence) else [right]), left
            )
            left = [
                Pitch(
                    pitch_class=operation(x.get_value(options), y.get_value(options)),
                    kwargs=options,
                )
                for (x, y) in pairs
            ]
        return left


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
    onset: ListSequence
    offset: ListSequence = field(default=None)
    rotate: int = field(default=0)
    evaluated_values: list = field(default=None)

    def evaluate(self, options):
        """Evaluate values using euclidean spread"""
        onset_values = [
            val for val in self.onset.values if not isinstance(val, Whitespace)
        ]
        onset_length = len(onset_values)
        booleans = euclidian_rhythm(self.pulses, self.length, self.rotate)
        self.evaluated_values = []

        if self.offset is not None:
            offset_values = [
                val for val in self.offset.values if not isinstance(val, Whitespace)
            ]
            offset_length = len(offset_values)

        on_i = 0
        off_i = 0

        for i in range(self.length):
            if booleans[i]:
                value = onset_values[on_i % onset_length]
                on_i += 1
            else:
                if self.offset is None:
                    value = Rest(duration=options["duration"])
                else:
                    value = offset_values[off_i % offset_length]
                off_i += 1

            self.evaluated_values.append(value)


@dataclass(kw_only=True)
class RepeatedSequence(Sequence):
    """Class for repeats"""

    repeats: RandomInteger | Integer = field(default_factory=Integer(value=1, text="1"))
    wrap_start: str = field(default="[:", repr=False)
    wrap_end: str = field(default=":]", repr=False)
    local_options: dict = field(default_factory=dict, init=False)

    evaluated_values: list = None

    def __post_init__(self):
        super().__post_init__()
        self.evaluated_values = list(self.evaluate())

    def evaluate(self):
        """Evaluate repeated sequence partially. Leaves Cycles intact."""
        for item in self.values:
            if isinstance(item, Sequence):
                if isinstance(item, ListOperation):
                    yield from item.evaluate_tree(self.local_options, True)
                else:
                    yield from item
            elif isinstance(item, Cyclic):
                yield item  # Return the cycle instead of values
            elif isinstance(item, Modification):
                self.local_options = self.local_options | item.as_options()
            elif isinstance(item, Rest):
                yield item.get_updated_item(self.local_options)
            elif isinstance(item, (Event, RandomInteger)):
                yield Pitch(pitch_class=item.get_value(self.local_options), kwargs=self.local_options)
