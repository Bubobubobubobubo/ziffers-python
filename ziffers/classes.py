from dataclasses import dataclass, asdict

@dataclass
class Meta:
    text: str

@dataclass
class Duration(Meta):
    dur: float

@dataclass
class Octave(Meta):
    oct: int

@dataclass
class Event(Meta):
    dur: float = None

@dataclass
class Pitch(Event):
    pc: int = None
    dur: float = None
    oct: int = None

@dataclass
class RandomPitch(Event):
    pc: int = None
    

@dataclass
class Chord(Event):
    pcs: list[Pitch] = None
    
@dataclass
class Function(Event):
    run: str = None

@dataclass
class Ziffers:
    values: list[Event]
    dict = asdict
    text: str = None
    def __post_init__(self):
        self.text = self.collect_text()
    def collect_text(self):
        return "".join([val.text for val in self.values])

@dataclass
class Sequence(Meta):
    values: list[Event]

@dataclass
class Subdivision(Meta):
    values: list[Event]

@dataclass
class Cyclic(Sequence):
    cycle: int = 0

@dataclass
class RandomPitch(Meta):
    min: int
    max: int

@dataclass
class Range(Meta):
    start: int
    end: int