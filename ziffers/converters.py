"""Collection of converters"""
from ziffers import zparse, Ziffers, Pitch, Rest, Chord

try:
    from music21 import converter, note, stream, meter, chord, environment
    music21_imported: bool = True
except ImportError:
    music21_imported: bool = False

try:
    import ctcsound
    csound_imported: bool = True
except (ImportError, TypeError) as Error:
    csound_imported: bool = False

def freq_to_pch(freq: float) -> str:
    "Format frequency to Csound PCH format"
    return f"{freq:.2f}"

# Csound score example: i1 0 1 0.5 8.00
# 1. The first number is the instrument number. In this case it is instrument 1.
# 2. The second number is the start time in seconds. In this case it is 0 seconds.
# 3. The third number is the duration in seconds. In this case it is 1 second.
# 4. The fourth number is the amplitude. In this case it is 0.5.
# 5. The fifth number is the frequency. In this case it is 8 Hz.

def freqs_and_durations_to_csound_score(pairs: list[list[float|list[float], float|list[float]]], bpm: int=80, amp: float=0.5, instr: (int|str)=1) -> str:
    """Tranforms list of lists containing frequencies and note lengths to csound score format.
       Note lengths are transformed in seconds with the bpm.
       Start time in seconds is calculated and summed from the note lengths.
       If frequency is None, then it is a rest.
       If frequency is a list, then it is a chord.
       
       Example input: [[261.6255653005986, 0.5], [None, 0.25], [440.0, 0.125], [[261.6255653005986, 329.62755691286986, 391.9954359817492], [0.25, 0.125, 0.25]]]"""
    score = ""
    instr = f'"{instr}"' if isinstance(instr, str) else instr
    start_time = 0
    for pair in pairs:
        if isinstance(pair[0], list):
            for freq, dur in zip(pair[0], pair[1]):
                score += f"i {instr} {start_time} {dur * 4 * 60 / bpm} {amp} {freq_to_pch(freq)}\n"
            start_time += max(pair[1]) * 4 * 60 / bpm
        else:
            if pair[0] is None:
                score += f"i {instr} {start_time} {pair[1] * 4 * 60 / bpm} {amp} 0\n"
            else:
                score += f"i {instr} {start_time} {pair[1] * 4 * 60 / bpm} {amp} {freq_to_pch(pair[0])}\n"
            start_time += pair[1] * 4 * 60 / bpm
    return score
    
def to_csound_score(expression: str | Ziffers, bpm: int=80, amp: float=0.5, instr: (int|str)=1) -> str:
    """ Transform Ziffers object to Csound score """
    if not csound_imported:
        raise ImportError("Install Csound library")

    if isinstance(expression, Ziffers):
        score = freqs_and_durations_to_csound_score(expression.freq_pairs(),bpm,amp,instr)
    else:
        parsed = zparse(expression)
        score = freqs_and_durations_to_csound_score(parsed.freq_pairs(),bpm,amp,instr)

    return score

def to_music21(expression: str | Ziffers, **options):
    """Helper for passing options to the parser"""

    if not music21_imported:
        raise ImportError("Install Music21 library")

    # Register the ZiffersMusic21 converter
    converter.registerSubconverter(ZiffersMusic21)

    if isinstance(expression, Ziffers):
        if options:
            options["preparsed"] = expression
        else:
            options = {"preparsed": expression}
        options = {"ziffers": options}
        return converter.parse("PREPARSED", format="ziffers", keywords=options)

    if options:
        options = {"ziffers": options}
        return converter.parse(expression, format="ziffers", keywords=options)

    test = converter.parse(expression, format="ziffers")
    return test


def set_musescore_path(path: str):
    """Helper for setting the Musescore path"""
    settings = environment.UserSettings()
    # Default windows path:
    # 'C:\\Program Files\\MuseScore 3\\bin\\MuseScore3.exe'
    settings["musicxmlPath"] = path
    settings["musescoreDirectPNGPath"] = path


if music21_imported:

    # pylint: disable=locally-disabled, invalid-name, unused-argument, attribute-defined-outside-init
    class ZiffersMusic21(converter.subConverters.SubConverter):
        """Ziffers converter to Music21"""

        registerFormats = ("ziffers",)
        registerInputExtensions = ("zf",)

        def parseData(self, dataString, number=None):
            """Parses Ziffers string to Music21 object"""
            # Look for options in keywords object
            keywords = self.keywords["keywords"]
            if "ziffers" in keywords:
                options = keywords["ziffers"]
                if "preparsed" in options:
                    parsed = options["preparsed"]
                else:
                    parsed = zparse(dataString, **options)
            else:
                parsed = zparse(dataString)

            note_stream = stream.Part()
            if "time" in options:
                m_item = meter.TimeSignature(options["time"])  # Common time
            else:
                m_item = meter.TimeSignature("c")  # Common time

            note_stream.insert(0, m_item)
            for item in parsed:
                if isinstance(item, Pitch):
                    m_item = note.Note(item.note)
                    m_item.duration.quarterLength = item.duration * 4
                elif isinstance(item, Rest):
                    m_item = note.Rest(item.duration * 4)
                elif isinstance(item, Chord):
                    m_item = chord.Chord(item.notes)
                    m_item.duration.quarterLength = item.duration * 4
                note_stream.append(m_item)
            # TODO: Is this ok?
            self.stream = note_stream.makeMeasures()