""" Ziffers classes for the parsed notation """
from dataclasses import dataclass, field, replace, asdict
from itertools import product, islice, cycle
from math import floor
import operator
import random
from copy import deepcopy
from .defaults import DEFAULT_OPTIONS
from .scale import note_from_pc, midi_to_pitch_class, midi_to_freq, get_scale_length
from .common import euclidian_rhythm


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
                    else:
                        setattr(self, key, value)
                elif getattr(self, key) is None:
                    local_value = self.local_options.get(key, False)
                    if local_value:
                        setattr(self, key, local_value)
                    else:
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


@dataclass
class Rest(Event):
    """Class for rests"""


@dataclass(kw_only=True)
class Pitch(Event):
    """Class for pitch in time"""

    pitch_class: int
    octave: int = field(default=None)
    modifier: int = field(default=None)
    note: int = field(default=None)
    key: str = field(default=None)
    scale: str | list = field(default=None)
    freq: float = field(default=None)
    beat: float = field(default=None)

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

    def get_notes(self) -> int:
        """Return notes"""
        return self.note

    def get_octaves(self) -> int:
        """Return octave"""
        return self.octave

    def get_beats(self) -> float:
        """Return beats"""
        return self.beat

    def get_durations(self) -> float:
        """Return duration"""
        return self.duration

    def get_freqs(self) -> float:
        """Return frequencies"""
        return self.freq


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
    freqs: list[float] = field(default=None, init=False)
    octaves: list[int] = field(default=None, init=False)
    durations: list[float] = field(default=None, init=False)
    beats: list[float] = field(default=None, init=False)

    def __post_init__(self):
        if self.inversions is not None:
            self.invert(self.inversions)

    def set_notes(self, notes: list[int]):
        """Set notes to the class"""
        self.notes = notes

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

    def update_notes(self, options):
        """Update notes"""
        pitches, notes, freqs, octaves, durations, beats = ([] for _ in range(6))

        # Update notes
        for pitch in self.pitch_classes:
            pitch.update_options(options)
            pitch.update_note()

        # Sort by generated notes
        self.pitch_classes = sorted(self.pitch_classes, key=lambda x: x.note)

        # Create helper lists
        for pitch in self.pitch_classes:
            pitches.append(pitch.pitch_class)
            notes.append(pitch.note)
            freqs.append(pitch.freq)
            octaves.append(pitch.octave)
            durations.append(pitch.duration)
            beats.append(pitch.beat)

        self.pitches = pitches
        self.notes = notes
        self.freqs = freqs
        self.octaves = octaves
        self.duration = durations
        self.beats = beats

    def get_pitches(self) -> list:
        """Return pitch classes"""
        return self.pitches

    def get_notes(self) -> list:
        """Return notes"""
        return self.notes

    def get_octaves(self) -> list:
        """Return octave"""
        return self.octaves

    def get_beats(self) -> float:
        """Return beats"""
        return self.beats

    def get_durations(self) -> float:
        """Return duration"""
        return self.durations

    def get_freqs(self) -> float:
        """Return frequencies"""
        return self.freqs


@dataclass(kw_only=True)
class RomanNumeral(Event):
    """Class for roman numbers"""

    value: str = field(default=None)
    chord_type: str = field(default=None)
    notes: list[int] = field(default_factory=[])
    pitch_classes: list = None
    inversions: int = None

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
class VariableAssignment(Item):
    """Class for defining variables"""

    variable: str
    value: Item
    pre_eval: bool


@dataclass(kw_only=True)
class Variable(Item):
    """Class for using variables"""

    name: str


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
        self.update_local_options()

    def __getitem__(self, index):
        return self.values[index]

    def update_local_options(self):
        """Update value attributes from dict"""
        if self.local_options:
            for obj in self.values:
                if isinstance(obj, Event):
                    if obj.local_options:
                        obj.local_options = (
                            obj.local_options | self.local_options.copy()
                        )
                    else:
                        obj.local_options = self.local_options.copy()

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
                    item.evaluate_values(options)
                    repeats = item.repeats.get_value(options)
                    repeats = _resolve_repeat_value(repeats)
                    yield from _normal_repeat(item.evaluated_values, repeats, options)
                elif isinstance(item, RepeatedListSequence):
                    repeats = item.repeats.get_value(options)
                    repeats = _resolve_repeat_value(repeats)
                    yield from _generative_repeat(item, repeats, options)
                elif isinstance(item, Subdivision):
                    item.evaluate_values(options)
                    yield item
                else:
                    yield from item.evaluate_tree(options)
            elif isinstance(item, VariableAssignment):
                if item.pre_eval:
                    pre_options = options.copy()
                    pre_options["pre_eval"] = True
                    options[item.variable.name] = Sequence(
                        values=list(_resolve_item(item.value, pre_options))
                    )
                else:
                    options[item.variable.name] = item.value
            elif isinstance(item, Variable):
                if options[item.name]:
                    variable = deepcopy(options[item.name])
                    yield from _resolve_item(variable, options)
            elif isinstance(item, Range):
                yield from item.evaluate(options)
            elif isinstance(item, Cyclic):
                yield from _resolve_item(item.get_value(), options)
            elif isinstance(item, Euclid):
                yield from _euclidean_items(item, options)
            elif isinstance(item, Modification):
                options = _parse_options(item, options)
            elif isinstance(item, Meta):  # Filters whitespace
                yield _update_item(item, options)

        def _resolve_repeat_value(item):
            while isinstance(item, Cyclic):
                item = item.get_value(options)
            if isinstance(item, Pitch):
                return item.get_value(options)
            if not isinstance(item, Integer):
                return 2
            return item

        def _update_item(item, options):
            """Update or create new pitch"""
            if set(("key", "scale")) <= options.keys():
                if isinstance(item, Pitch):
                    item.update_options(options)
                    item.update_note()
                    if options.get("pre_eval", False):
                        item.duration = options["duration"]
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

        def _generative_repeat(tree: list, times: int, options: dict):
            """Repeats items and generates new random values"""
            for _ in range(times):
                for item in tree.evaluate_tree(options):
                    yield from _resolve_item(item, options)

        def _normal_repeat(tree: list, times: int, options: dict):
            """Repeats items with the same random values"""
            for _ in range(times):
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

        def _parse_options(current: Item, options: dict) -> dict:
            """Update options based on current item"""
            if isinstance(current, (OctaveChange, DurationChange)):
                options[current.key] = current.value
            elif isinstance(current, OctaveAdd):
                if current.key in options:  # Add to existing value
                    options[current.key] += current.value
                else:  # Create value if not existing
                    options[current.key] = current.value
            return options

        def _create_pitch_without_note(current: Item, options: dict) -> Pitch:
            return Pitch(pitch_class=current.get_value(options))

        def _create_pitch(current: Item, options: dict) -> Pitch:
            """Create pitch based on values and options"""

            merged_options = options | self.local_options

            if "modifier" in merged_options:
                c_modifier = merged_options["modifier"]
            else:
                c_modifier = 0

            if hasattr(current, "modifier") and current.modifier is not None:
                c_modifier += current.modifier

            if "octave" in merged_options:
                c_octave = merged_options["octave"]
                if "octave" in options:
                    c_octave = options["octave"] + c_octave
            else:
                c_octave = 0

            if hasattr(current, "octave") and current.octave is not None:
                c_octave += current.octave

            current_value = current.get_value(merged_options)

            note = note_from_pc(
                root=merged_options["key"],
                pitch_class=current_value,
                intervals=merged_options["scale"],
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
                kwargs=merged_options,
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
                inversions=current.inversions,
            )

            chord.update_notes(options)

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

    options: dict = field(default_factory=DEFAULT_OPTIONS.copy())
    start_options: dict = None
    loop_i: int = field(default=0, init=False)
    cycle_i: int = field(default=0, init=False)
    iterator = None
    current: Item = field(default=None)
    cycle_length: int = field(default=0, init=False)

    def __getitem__(self, index):
        self.loop_i = index % self.cycle_length
        new_cycle = floor(index / self.cycle_length)
        if new_cycle > self.cycle_i or new_cycle < self.cycle_i:
            self.re_eval()
            self.cycle_i = new_cycle
            self.cycle_length = len(self.evaluated_values)
            self.loop_i = index % self.cycle_length
        return self.evaluated_values[self.loop_i]

    def __iter__(self):
        return self

    def __next__(self):
        self.current = next(self.iterator)
        self.loop_i += 1
        return self.current

    # pylint: disable=locally-disabled, dangerous-default-value
    def init_opts(self, options=None):
        """Evaluate the Ziffers tree using the options"""
        self.options.update(DEFAULT_OPTIONS.copy())
        if options:
            self.options.update(options)
        else:
            self.options = DEFAULT_OPTIONS.copy()

        self.start_options = self.options.copy()
        self.init_tree(self.options)

    def re_eval(self):
        """Re-evaluate the iterator"""
        self.options = self.start_options.copy()
        self.init_tree(self.options)

    def init_tree(self, options):
        """Initialize evaluated values and perform post-evaluation"""
        self.evaluated_values = list(self.evaluate_tree(options))
        self.evaluated_values = list(self.post_evaluation())
        self.iterator = iter(self.evaluated_values)
        self.cycle_length = len(self.evaluated_values)

    def post_evaluation(self):
        """Post-evaluation performs evaluation that can only be done after initial evaluation"""
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
        self.options = DEFAULT_OPTIONS.copy() | options

    def pitch_classes(self) -> list[int]:
        """Return list of pitch classes as ints"""
        return [
            val.get_pitches()
            for val in self.evaluated_values
            if isinstance(val, (Pitch, Chord))
        ]

    def notes(self) -> list[int]:
        """Return list of midi notes"""
        return [
            val.get_notes()
            for val in self.evaluated_values
            if isinstance(val, (Pitch, Chord))
        ]

    def durations(self) -> list[float]:
        """Return list of pitch durations as floats"""
        return [
            val.get_durations()
            for val in self.evaluated_values
            if isinstance(val, Event)
        ]

    def beats(self) -> list[float]:
        """Return list of pitch durations as floats"""
        return [
            val.get_beats() for val in self.evaluated_values if isinstance(val, Event)
        ]

    def pairs(self) -> list[tuple]:
        """Return list of pitches and durations"""
        return [
            (val.pitch_class, val.duration)
            for val in self.evaluated_values
            if isinstance(val, Pitch)
        ]

    def octaves(self) -> list[int]:
        """Return list of octaves"""
        return [
            val.get_octaves()
            for val in self.evaluated_values
            if isinstance(val, (Pitch, Chord))
        ]

    def freqs(self) -> list[int]:
        """Return list of octaves"""
        return [
            val.get_freqs()
            for val in self.evaluated_values
            if isinstance(val, (Pitch, Chord))
        ]


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

    full_duration: float = field(default=None, init=False)

    def evaluate_values(self, options):
        """Evaluate values and store to evaluated_values"""
        self.full_duration = options["duration"]
        self.evaluated_values = list(self.evaluate_tree(options))

    def evaluate_durations(self, duration=None):
        """Calculate new durations by dividing with the number of items in the sequence"""
        if duration is None:
            duration = self.full_duration
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
                yield Pitch(pitch_class=i, local_options=merged_options)
        elif self.start > self.end:
            for i in reversed(range(self.end, self.start + 1)):
                yield Pitch(pitch_class=i, local_options=merged_options)
        else:
            yield Pitch(pitch_class=self.start, local_options=merged_options)


@dataclass(kw_only=True)
class Operator(Item):
    """Class for math operators"""

    value: ...


@dataclass(kw_only=True)
class ListOperation(Sequence):
    """Class for list operations"""

    evaluated_values: list = None

    def evaluate(self, options=DEFAULT_OPTIONS.copy()):
        """Evaluates the operation"""

        def filter_operation(input_list, options):
            flattened_list = []

            for item in input_list:
                if isinstance(item, (list, Sequence)):
                    if isinstance(item, ListOperation):
                        flattened_list.extend(item.evaluated_values)
                    else:
                        flattened_list.append(filter_operation(item, options))
                elif isinstance(item, Cyclic):
                    value = item.get_value()
                    if isinstance(value, Sequence):
                        flattened_list.extend(filter_operation(value, options))
                    elif isinstance(value, (Event, RandomInteger, Integer)):
                        flattened_list.append(value)
                elif isinstance(item, Modification):
                    options = options | item.as_options()
                elif isinstance(item, Range):
                    flattened_list.extend(list(item.evaluate(options)))
                elif isinstance(item, (Event, RandomInteger, Integer)):
                    item.update_options(options)
                    flattened_list.append(item)

            if isinstance(input_list, Sequence):
                return replace(input_list, values=flattened_list)

            return flattened_list

        operators = self.values[1::2]  # Fetch every second operator element
        values = self.values[::2]  # Fetch every second list element
        values = filter_operation(values, options)  # Filter out
        if len(values) == 1:
            return values[0]  # If right hand doesnt contain anything sensible
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
                    kwargs=y.get_options(),
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

    evaluated_values: list = None

    def evaluate_values(self, options):
        """Evaluate values and store to evaluated_values"""
        self.evaluated_values = list(self.evaluate(options))

    def evaluate(self, options: dict):
        """Evaluate repeated sequence partially. Leaves Cycles intact."""
        self.local_options = options.copy()
        for item in self.values:
            if isinstance(item, Sequence):
                if isinstance(item, ListOperation):
                    yield from item.evaluate_tree(self.local_options, True)
                elif isinstance(item, RepeatedSequence):
                    yield item
                else:
                    yield from item
            elif isinstance(item, Cyclic):
                yield item  # Return the cycle instead of values
            elif isinstance(item, Modification):
                self.local_options = self.local_options | item.as_options()
            elif isinstance(item, Rest):
                yield item.get_updated_item(self.local_options)
            elif isinstance(item, Range):
                yield from item.evaluate(self.local_options)
            elif isinstance(item, (Event, RandomInteger)):
                yield Pitch(
                    pitch_class=item.get_value(self.local_options),
                    kwargs=self.local_options,
                )
