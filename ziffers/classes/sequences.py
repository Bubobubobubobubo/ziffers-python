""" Sequence classes for Ziffers """
from dataclasses import dataclass, field, replace
from itertools import product
from types import LambdaType
from copy import deepcopy
from ..defaults import DEFAULT_OPTIONS
from ..common import cyclic_zip, euclidian_rhythm
from ..scale import note_from_pc, midi_to_freq
from .items import (
    Meta,
    Item,
    Event,
    DurationChange,
    OctaveChange,
    OctaveAdd,
    Pitch,
    Rest,
    RandomPitch,
    Chord,
    RomanNumeral,
    Cyclic,
    RandomInteger,
    Range,
    Integer,
    VariableAssignment,
    Variable,
    VariableList,
    Measure,
    Function,
    Modification,
    Whitespace,
    Sample,
)


# TODO: Could be refactored to each class?
def resolve_item(item: Meta, options: dict):
    """Resolve cyclic value"""
    if isinstance(item, Sequence):
        if isinstance(item, ListOperation):
            yield from item.evaluate(options)
        elif isinstance(item, (RepeatedSequence, RepeatedListSequence)):
            yield from item.resolve_repeat(options)
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
                values=list(resolve_item(item.value, pre_options))
            )
        else:
            options[item.variable.name] = item.value
    elif isinstance(item, Variable):
        if options[item.name]:
            if item.name in options:
                opt_item = options[item.name]
                if isinstance(opt_item, LambdaType):
                    yield Function(
                        run=opt_item,
                        text=item.text,
                        kwargs=(options | item.local_options),
                    )
                elif isinstance(opt_item, str):
                    yield Sample(
                        name=opt_item,
                        text=item.text,
                        kwargs=(options | item.local_options),
                    )
                variable = deepcopy(opt_item)
                yield from resolve_item(variable, options)
    elif isinstance(item, VariableList):
        seqlist = []
        for var in item.values:
            if var.name in options:
                opt_item = options[var.name]
                if isinstance(opt_item, LambdaType):
                    seqlist.append(
                        Function(
                            run=opt_item,
                            text=var.text,
                            kwargs=(options | var.local_options),
                        )
                    )
                elif isinstance(opt_item, str):
                    seqlist.append(
                        Sample(
                            name=opt_item,
                            text=var.text,
                            kwargs=(options | var.local_options),
                        )
                    )
                elif isinstance(opt_item, Sequence):
                    seqlist.append(opt_item)
        if len(seqlist) > 0:
            yield PolyphonicSequence(values=seqlist)
    elif isinstance(item, Range):
        yield from item.evaluate(options)
    elif isinstance(item, Cyclic):
        yield from resolve_item(item.get_value(), options)
    elif isinstance(item, Euclid):
        yield from euclidean_items(item, options)
    elif isinstance(item, Modification):
        update_modifications(item, options)
    elif isinstance(item, Measure):
        item.reset_options(options)
    elif isinstance(item, Meta):  # Filters whitespace
        yield update_item(item, options)


def resolve_integer_value(item, options):
    """Helper for resolving integer value of different types"""
    while isinstance(item, Cyclic):
        item = item.get_value(options)
    if isinstance(item, Pitch):
        return item.get_value(options)
    if isinstance(item, Integer):
        return item.get_value(options)
    return item


def update_item(item, options):
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
            item = create_pitch(item, options)
        elif isinstance(item, Chord):
            item.update_options(options)
            item.update_notes(options)
        elif isinstance(item, RomanNumeral):
            item = item.evaluate_chord(options)
    return item


def euclidean_items(euclid: Item, options: dict):
    """Loops values from generated euclidean sequence"""
    euclid.evaluate(options)
    for item in euclid.evaluated_values:
        yield from resolve_item(item, options)


def update_modifications(current: Item, options: dict) -> dict:
    """Update options based on current item"""
    if isinstance(current, (OctaveChange, DurationChange)):
        options[current.key] = current.value
    elif isinstance(current, OctaveAdd):
        if current.key in options:  # Add to existing value
            options[current.key] += current.value
        else:  # Create value if not existing
            options[current.key] = current.value


def create_pitch(current: Item, options: dict) -> Pitch:
    """Create pitch based on values and options"""

    merged_options = options | current.local_options

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

    def __len__(self):
        return len(self.values)

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

        # Start of the main function: Evaluate and flatten the Ziffers object tree
        values = self.evaluated_values if eval_tree else self.values
        for item in values:
            yield from resolve_item(item, options)

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
class PolyphonicSequence:
    """Class for polyphonic sequence"""

    values: list


@dataclass(kw_only=True)
class ListSequence(Sequence):
    """Class for Ziffers list sequences"""

    wrap_start: str = field(default="(", repr=False)
    wrap_end: str = field(default=")", repr=False)


@dataclass(kw_only=True)
class RepeatedListSequence(Sequence):
    """Class for Ziffers list sequences"""

    repeats: RandomInteger | Integer = field(default_factory=Integer(value=1, text="1"))
    wrap_start: str = field(default="(:", repr=False)
    wrap_end: str = field(default=":)", repr=False)

    def resolve_repeat(self, options: dict):
        """Repeats items and generates new random values"""
        repeats = self.repeats.get_value(options)
        if not isinstance(repeats, int):
            repeats = resolve_integer_value(repeats, options)
        for _ in range(repeats):
            for item in self.evaluate_tree(options):
                yield from resolve_item(item, options)


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
class ListOperation(Sequence):
    """Class for list operations"""

    evaluated_values: list = None

    def evaluate(self, options=DEFAULT_OPTIONS.copy()):
        """Evaluates the operation"""

        def _filter_whitespace(input_list):
            for item in input_list:
                if isinstance(item, Meta):
                    yield item

        def _filter_operation(input_list, options):
            """Filter and evaluate values"""
            flattened_list = []
            for item in input_list:
                if isinstance(item, (list, Sequence)):
                    if isinstance(item, ListOperation):
                        flattened_list.extend(item.evaluated_values)
                    elif isinstance(item, Subdivision):
                        item.evaluate_values(options)
                        flattened_list.extend(list(item.evaluate_durations()))
                    elif isinstance(item, RepeatedListSequence):
                        flattened_list.extend(list(item.resolve_repeat(options)))
                    else:
                        flattened_list.append(_filter_operation(item, options))
                elif isinstance(item, Cyclic):
                    value = item.get_value()
                    if isinstance(value, Sequence):
                        flattened_list.extend(_filter_operation(value, options))
                    elif isinstance(value, (Event, RandomInteger, Integer)):
                        flattened_list.append(value)
                elif isinstance(item, Modification):
                    options = options | item.as_options()
                elif isinstance(item, RomanNumeral):
                    item = item.evaluate_chord(options)
                    flattened_list.append(item)
                elif isinstance(item, Range):
                    flattened_list.extend(list(item.evaluate(options)))
                elif isinstance(item, (Event, RandomInteger, Integer)):
                    item.update_options(options)
                    flattened_list.append(item)

            if isinstance(input_list, Sequence):
                return replace(input_list, values=flattened_list)

            return flattened_list

        def _vertical_arpeggio(left, right, options):
            """Vertical arpeggio operation, eg. (135)@(q 1 2 021)"""
            left = _filter_operation(left, options)
            right = _filter_operation(right, options)
            if not isinstance(left, list):
                left = list(left.evaluate_tree(options))
            if not isinstance(right, list):
                right = list(right.evaluate_tree(options))
            arp_items = []

            for item in left:
                for index in right:
                    pcs = item.pitch_classes
                    if isinstance(index, Pitch):
                        new_pitch = deepcopy(pcs[index.get_value(options) % len(pcs)])
                        new_pitch.duration = index.duration
                        arp_items.append(new_pitch)
                    else:  # Should be a chord
                        new_pitches = []
                        for pitch in index.pitch_classes:
                            new_pitch = deepcopy(
                                pcs[pitch.get_value(options) % len(pcs)]
                            )
                            new_pitch.duration = pitch.duration
                            new_pitches.append(new_pitch)
                        new_chord = Chord(pitch_classes=new_pitches, kwargs=options)
                        new_chord.update_notes()
                        new_chord.text = "".join(
                            [val.text for val in new_chord.pitch_classes]
                        )
                        arp_items.append(new_chord)

            return Sequence(values=arp_items)

        def _horizontal_arpeggio(left, right, options):
            """Horizontal arpeggio operation, eg. (1 2 3 4)#(0 3 2 1)"""
            left = _filter_operation(left, options)
            right = _filter_operation(right, options)
            left = list(left.evaluate_tree(options))
            right = list(right.evaluate_tree(options))
            arp_items = []
            for index in right:
                new_item = deepcopy(left[index.get_value(options) % len(left)])
                arp_items.append(new_item)
            return Sequence(values=arp_items)

        def _cyclic_zip(left, right, options):
            """Cyclic zip operaiton, eg. (q e)<>(1 2 3)"""
            left = list(_filter_whitespace(left))
            right = list(_filter_whitespace(right))
            result = Sequence(values=cyclic_zip(left, right))
            return _filter_operation(result, options)

        def _python_operations(left, right, options):
            """Python math operations"""

            def __chord_operation(chord, pitch_y, yass, options):
                """Operation for single chords"""
                new_pitches = []
                pitch_y = pitch_y.get_value(options)
                for pitch_x in chord.pitch_classes:
                    pitch_x = pitch_x.pitch_class
                    pitch_y = resolve_integer_value(pitch_y, options)
                    new_pitch = Pitch(
                        pitch_class=operation(
                            pitch_y if yass else pitch_x, pitch_x if yass else pitch_y
                        ),
                        kwargs=options,
                    )
                    new_pitches.append(new_pitch)
                new_chord = Chord(pitch_classes=new_pitches, kwargs=options)
                new_chord.update_notes()
                return new_chord

            # _python_operation starts. Filter & evaluate items.

            left = _filter_operation(left, options)
            if isinstance(right, Sequence):
                right = _filter_operation(right, options)
            elif isinstance(right, Cyclic):
                right = right.get_value(options)

            # Create product of items.
            pairs = product(
                (right.values if isinstance(right, Sequence) else [right]), left
            )

            results = []
            for first, second in pairs:
                if isinstance(first, Chord) and isinstance(second, Chord):
                    new_pitches = []
                    for pitch_x in first.pitch_classes:
                        for pitch_y in second.pitch_classes:
                            new_pitch = Pitch(
                                pitch_class=operation(
                                    pitch_x.pitch_class, pitch_y.pitch_class
                                ),
                                kwargs=options,
                            )
                            new_pitches.append(new_pitch)
                        new_chord = Chord(pitch_classes=new_pitches, kwargs=options)
                        new_chord.update_notes()
                        outcome = new_chord
                elif isinstance(first, Chord):
                    outcome = __chord_operation(first, second, False, options)
                elif isinstance(second, Chord):
                    outcome = __chord_operation(second, first, True, options)
                else:
                    outcome = Pitch(
                        pitch_class=operation(
                            first.get_value(options), second.get_value(options)
                        ),
                        kwargs=second.get_options(),
                    )
                results.append(outcome)
            return results

        # Start of the evaluate() function

        operators = self.values[1::2]  # Fetch every second operator element
        values = self.values[::2]  # Fetch every second list element
        # values = _filter_operation(values, options)  # Filter out
        if len(values) == 1:
            return values[0]  # If right hand doesnt contain anything sensible
        left = values[0]  # Start results with the first array

        for i, operand in enumerate(operators):
            operation = operand.value
            right = values[i + 1]
            if isinstance(operation, str):
                if operation == "vertical":
                    left = _vertical_arpeggio(left, right, options)
                elif operation == "horizontal":
                    left = _horizontal_arpeggio(left, right, options)
                if operation == "zip":
                    left = _cyclic_zip(left, right, options)
            else:
                left = _python_operations(left, right, options)
        return left


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
class RepeatedSequence(Sequence):
    """Class for repeats"""

    repeats: RandomInteger | Integer = field(default_factory=Integer(value=1, text="1"))
    wrap_start: str = field(default="[:", repr=False)
    wrap_end: str = field(default=":]", repr=False)

    evaluated_values: list = None

    def resolve_repeat(self, options):
        """Resolves all items"""
        self.evaluate_values(options)
        repeats = self.repeats.get_value(options)
        if not isinstance(repeats, int):
            repeats = resolve_integer_value(repeats, options)
        for _ in range(repeats):
            for item in self.evaluated_values:
                yield from resolve_item(item, options)

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
                elif isinstance(item, Subdivision):
                    item.evaluate_values(options)
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
            elif isinstance(item, (Pitch, Chord, RomanNumeral)):
                yield item
            elif isinstance(item, (Event, RandomInteger)):
                yield Pitch(
                    pitch_class=item.get_value(self.local_options),
                    kwargs=self.local_options,
                )


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
