"""Root class for Ziffers object"""

from dataclasses import dataclass, field
from itertools import islice, cycle
from ..defaults import DEFAULT_OPTIONS
from .items import Item, Pitch, Chord, Event, Rest
from .sequences import Sequence, Subdivision


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
        new_cycle = index // self.cycle_length
        # Re-evaluate if the prior loop has ended
        if new_cycle > self.cycle_i or new_cycle < self.cycle_i:
            self.re_eval()
            self.cycle_i = new_cycle
            self.cycle_length = len(self.evaluated_values)
            self.loop_i = index % self.cycle_length
        return self.evaluated_values[self.loop_i]

    def __len__(self):
        return len(self.evaluated_values)

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
        self.options["start_options"] = self.start_options
        self.init_tree(self.options)

    def re_eval(self):
        """Re-evaluate the iterator"""
        self.options = self.start_options.copy()
        self.options["start_options"] = self.start_options
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
            val.get_pitch_class()
            for val in self.evaluated_values
            if isinstance(val, (Pitch, Chord, Rest))
        ]

    def pitch_bends(self) -> list[int]:
        """Return list of pitch bend values"""
        return [
            val.get_pitch_bend()
            for val in self.evaluated_values
            if isinstance(val, (Pitch, Chord, Rest))
        ]

    def notes(self) -> list[int]:
        """Return list of midi notes"""
        return [
            val.get_note()
            for val in self.evaluated_values
            if isinstance(val, (Pitch, Chord, Rest))
        ]

    def durations(self) -> list[float]:
        """Return list of pitch durations as floats"""
        return [
            val.get_duration()
            for val in self.evaluated_values
            if isinstance(val, Event)
        ]

    def total_duration(self) -> float:
        """Return total duration"""
        return sum(
            [val.duration for val in self.evaluated_values if isinstance(val, Event)]
        )

    def total_beats(self) -> float:
        """Return total beats"""
        return sum(self.beats())

    def beats(self) -> list[float]:
        """Return list of pitch durations as floats"""
        return [
            val.get_beat() for val in self.evaluated_values if isinstance(val, Event)
        ]

    def pairs(self) -> list[tuple]:
        """Return list of pitches and durations"""
        return [
            (val.get_pitch_class(), val.get_duration())
            for val in self.evaluated_values
            if isinstance(val, Pitch)
        ]

    def octaves(self) -> list[int]:
        """Return list of octaves"""
        return [
            val.get_octave()
            for val in self.evaluated_values
            if isinstance(val, (Pitch, Chord, Rest))
        ]

    def freqs(self) -> list[int]:
        """Return list of octaves"""
        return [
            val.get_freq()
            for val in self.evaluated_values
            if isinstance(val, (Pitch, Chord, Rest))
        ]

    def collect(self, num: int = None, keys: str | list = None) -> list:
        """Collect n items from parsed Ziffers"""
        if num is None:
            num = len(self.evaluated_values)
        if keys is None or isinstance(keys, str):
            keys = [keys]
        all_items = []
        values = []
        for key in keys:
            for i in range(num):
                if key is not None:
                    values.append(getattr(self[i], key, None))
                else:
                    values.append(self[i])
            all_items.append(values)
            values = []
        if len(all_items) > 1:
            return all_items
        if len(all_items) == 1:
            return all_items[0]
        return None
