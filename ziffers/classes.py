from dataclasses import dataclass, field
import operator
from typing import Any

@dataclass
class Meta:
    ''' Abstract class for all Ziffers items'''
    def update(self, new_values):
        ''' Update attributes from dict '''
        for key, value in new_values.items():
            if hasattr(self, key):
                setattr(self, key, value)

@dataclass
class Item(Meta):
    ''' Class for all Ziffers text based items '''
    text: str

@dataclass
class Whitespace(Item):
    ''' Class for whitespace '''

@dataclass
class DurationChange(Item):
    ''' Class for changing duration '''
    dur: float

@dataclass
class OctaveChange(Item):
    ''' Class for changing octave '''
    oct: int

@dataclass
class OctaveMod(Item):
    ''' Class for modifying octave '''
    oct: int

@dataclass
class Event(Item):
    ''' Abstract class for events with duration '''
    dur: float = None

@dataclass
class Pitch(Event):
    ''' Class for pitch in time '''
    pc: int = None
    dur: float = None
    oct: int = None

@dataclass
class RandomPitch(Event):
    ''' Class for random pitch '''
    pc: int = None

@dataclass
class RandomPercent(Item):
    ''' Class for random percent '''
    percent: float = None

@dataclass
class Chord(Event):
    ''' Class for chords '''
    pcs: list[Pitch] = None
    
@dataclass
class Function(Event):
    ''' Class for functions '''
    run: str = None

class dataclass_property(property): # pylint: disable=invalid-name
    ''' Hack for dataclass setters '''
    def __set__(self, __obj: Any, __value: Any) -> None:
        if isinstance(__value, self.__class__):
            return None
        return super().__set__(__obj, __value)

@dataclass
class Sequence(Meta):
    ''' Class for sequences of items'''
    values: list[Item]
    text: str = field(init=False)
    _text: str = field(default=None, init=False, repr=False)

    @dataclass_property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str) -> None:
        self._text = text

    wrap_start: str = field(default=None, repr=False)
    wrap_end: str = field(default=None, repr=False)

    def __post_init__(self):
        self.text = self.collect_text()

    def update_values(self, new_values):
        ''' Update value attributes from dict '''
        for key, value in new_values.items():
            for obj in self.values:
                if key!="text" and hasattr(obj, key):
                    setattr(obj, key, value)
    
    def collect_text(self) -> str:
        text = "".join([val.text for val in self.values])
        if self.wrap_start != None:
            text = self.wrap_start + text
        if self.wrap_end != None:
            text = text + self.wrap_end
        return text

    def pcs(self) -> list[int]:
        return [val.pc for val in self.values if type(val) is Pitch]
    
    def durations(self) -> list[float]:
        return [val.dur for val in self.values if type(val) is Pitch]
    
    def pairs(self) -> list[tuple]:
        return [(val.pc,val.dur) for val in self.values if type(val) is Pitch]

@dataclass
class ListSequence(Sequence):
    ''' Class for Ziffers list sequences '''
    wrap_start: str = field(default="(", repr=False)
    wrap_end: str = field(default=")", repr=False)

@dataclass
class RepeatedListSequence(Sequence):
    ''' Class for Ziffers list sequences '''
    repeats: Item = None
    wrap_start: str = field(default="(:", repr=False)
    wrap_end: str = field(default=":)", repr=False)

@dataclass
class Subdivision(Item):
    ''' Class for subdivisions '''
    values: list[Event]

@dataclass
class Cyclic(Sequence):
    ''' Class for cyclic sequences'''
    cycle: int = 0
    wrap_start: str = field(default="<", repr=False)
    wrap_end: str = field(default=">", repr=False)
    
    def __post_init__(self):
        super().__post_init__()
        # TODO: Do spaced need to be filtered out?
        self.values = [val for val in self.values if type(val)!=Item]

@dataclass
class RandomInteger(Item):
    ''' Class for random integer '''
    min: int
    max: int

@dataclass
class Range(Item):
    ''' Class for range '''
    start: int
    end: int

ops = {
    '+' : operator.add,
    '-' : operator.sub,
    '*' : operator.mul,
    '/' : operator.truediv,
    '%' : operator.mod
}

@dataclass
class Operator(Item):
    ''' Class for math operators '''
    value: ... = field(init=False, repr=False)   
    def __post_init__(self):
        self.value = ops[self.text]

@dataclass
class ListOperation(Sequence):
    ''' Class for list operations '''
    def run(self):
        pass

@dataclass
class Operation(Item):
    ''' Class for lisp-like operations: (+ 1 2 3) etc. '''
    values: list
    operator: operator

@dataclass
class Eval(Sequence):
    ''' Class for evaluation notation '''
    result: ... = None
    wrap_start: str = field(default="{", repr=False)
    wrap_end: str = field(default="}", repr=False)
    def __post_init__(self):
        super().__post_init__()
        self.result = eval(self.text)

@dataclass
class Atom(Item):
    ''' Class for evaluable atoms'''
    value: ...

@dataclass
class Integer(Item):
    ''' Class for integers '''
    value: int

@dataclass
class Euclid(Item):
    ''' Class for euclidean cycles '''
    pulses: int
    length: int
    onset: list
    offset: list = None
    rotate: int = None

@dataclass
class RepeatedSequence(Sequence):
    ''' Class for repeats '''
    repeats: Item = None
    wrap_start: str = field(default="[:", repr=False)
    wrap_end: str = field(default=":]", repr=False)
    