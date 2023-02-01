from dataclasses import dataclass, asdict

@dataclass
class Meta:
    text: str

@dataclass
class DurationChange(Meta):
    dur: float

@dataclass
class OctaveChange(Meta):
    oct: int

@dataclass
class OctaveMod(Meta):
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
class RandomPercent(Meta):
    percent: float = None

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
    def collect_text(self) -> str:
        return "".join([val.text for val in self.values])
    def pcs(self) -> list[int]:
        return [val.pc for val in self.values if type(val) is Pitch]

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
class RandomInteger(Meta):
    min: int
    max: int

@dataclass
class Range(Meta):
    start: int
    end: int