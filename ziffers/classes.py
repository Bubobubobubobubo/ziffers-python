from dataclasses import dataclass, field
import operator
from typing import Any
import random
from .defaults import DEFAULT_OPTIONS
import itertools

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
                if getattr(self,key) == None:
                    setattr(self, key, value)

@dataclass
class Item(Meta):
    """Class for all Ziffers text based items"""

    text: str


@dataclass
class Whitespace(Item):
    """Class for whitespace"""

    item_type: str = None


@dataclass
class DurationChange(Item):
    """Class for changing duration"""

    value: float
    key: str = "duration"
    item_type: str = "change"

@dataclass
class OctaveChange(Item):
    """Class for changing octave"""

    value: int
    key: str = "octave"
    item_type: str = "change"


@dataclass
class OctaveMod(Item):
    """Class for modifying octave"""

    value: int
    key: str = "octave"
    item_type: str = "add"

@dataclass
class Event(Item):
    """Abstract class for events with duration"""

    duration: float = None


@dataclass
class Pitch(Event):
    """Class for pitch in time"""

    pc: int = None
    duration: float = None
    octave: int = None


@dataclass
class RandomPitch(Event):
    """Class for random pitch"""

    pc: int = None


@dataclass
class RandomPercent(Item):
    """Class for random percent"""

    percent: float = None


@dataclass
class Chord(Event):
    """Class for chords"""

    pcs: list[Pitch] = None


@dataclass
class Function(Event):
    """Class for functions"""

    run: str = None

@dataclass
class Sequence(Meta):
    """Class for sequences of items"""

    values: list[Item]
    text: str = None
    wrap_start: str = field(default=None, repr=False)
    wrap_end: str = field(default=None, repr=False)
    local_index: int = 0

    def __post_init__(self):
        self.text = self.collect_text()
        # TODO: Filter out whitespace if not needed?
        # self.values = list(filter(lambda elm: not isinstance(elm, Whitespace), self.values))

    def __iter__(self):
        return self
    
    def __next__(self):
        if self.local_index<len(self.values):
            next_item = self.values[self.local_index]
            self.local_index += 1
            return next_item
        else:
            self.local_index = 0
            raise StopIteration

    def update_values(self, new_values):
        """Update value attributes from dict"""
        for key, value in new_values.items():
            for obj in self.values:
                if key != "text" and hasattr(obj, key):
                    setattr(obj, key, value)

    def collect_text(self) -> str:
        text = "".join([val.text for val in self.values])
        if self.wrap_start != None:
            text = self.wrap_start + text
        if self.wrap_end != None:
            text = text + self.wrap_end
        return text

@dataclass
class ListSequence(Sequence):
    """Class for Ziffers list sequences"""

    wrap_start: str = field(default="(", repr=False)
    wrap_end: str = field(default=")", repr=False)


@dataclass
class RepeatedListSequence(Sequence):
    """Class for Ziffers list sequences"""

    repeats: Item = None
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
        self.values = [val for val in self.values if isinstance(val,Whitespace)]

    def value(self):
        return self.values[self.cycle]

    def next_cycle(self, cycle: int):
        self.cycle = self.cycle+1


@dataclass
class RandomInteger(Item):
    """Class for random integer"""

    min: int
    max: int

    def __post_init__(self):
        if self.min>self.max:
            new_max = self.min
            self.min = self.max
            self.max = new_max

    def value(self):
        return random.randint(self.min,self.max)


@dataclass
class Range(Item):
    """Class for range"""

    start: int = None
    end: int = None


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
class Integer(Item):
    """Class for integers"""

    value: int


@dataclass
class Euclid(Item):
    """Class for euclidean cycles"""

    pulses: int
    length: int
    onset: list
    offset: list = None
    rotate: int = None


@dataclass
class RepeatedSequence(Sequence):
    """Class for repeats"""

    repeats: Item = None
    wrap_start: str = field(default="[:", repr=False)
    wrap_end: str = field(default=":]", repr=False)

@dataclass
class Ziffers(Sequence):
    """Main class for holding options and the current state"""

    options: dict  = field(default_factory=DEFAULT_OPTIONS)
    loop_i: int = 0
    current: Item = None
    it: iter = None

    def __post_init__(self):
        super().__post_init__()
        self.it = iter(self.values)
    
    def __next__(self):
        try:
            self.current = next(self.it)

            # Skip whitespace and collect duration & octave changes  
            while isinstance(self.current,(Whitespace,DurationChange,OctaveChange,OctaveMod)):
                if self.current.item_type == "change":
                    self.options[self.current.key] = self.current.value
                elif self.current.item_type == "add":
                    if self.current.key in self.options:
                        self.options[self.current.key] += self.current.value
                    else:
                        self.options[self.current.key] = self.current.value
                    
                self.current = next(self.it)
        
        except StopIteration: # Start from the beginning
            self.current = next(self.it)
        
        self.current.update_new(self.options)        
        
        self.loop_i += 1
        return self.current

    def take(self,num: int) -> list:
        return list(itertools.islice(iter(self), num))

    def set_defaults(self,options: dict):
        self.options = DEFAULT_OPTIONS | options

    # TODO: Handle options and generated values
    def pcs(self) -> list[int]:
        return [val.pc for val in self.values if isinstance(val,Pitch)]

    def durations(self) -> list[float]:
        return [val.dur for val in self.values if isinstance(val,Pitch)]

    def pairs(self) -> list[tuple]:
        return [(val.pc,val.dur) for val in self.values if isinstance(val,Pitch)]

    def octaves(self) -> list[int]:
        return [val.octave for val in self.values if isinstance(val,Pitch)]