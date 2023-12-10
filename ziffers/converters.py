"""Collection of converters"""
from ziffers import zparse, Ziffers, Pitch, Rest, Chord, accidentals_from_note_name, MODES, MODE_ACCIDENTALS

try:
    from music21 import converter, note, stream, meter, chord, environment, tempo, key
    music21_imported: bool = True
except ImportError:
    music21_imported: bool = False

try:
    import ctcsound
    csound_imported: bool = True
except (ImportError, TypeError) as Error:
    csound_imported: bool = False

def ziffers_to_csound_score(ziffers: Ziffers, bpm: int=80, amp: float=1500, instr: (int|str)=1) -> str:
    """ Transform Ziffers object to Csound score in format:
        i {instrument} {start time} {duration} {amplitude} {frequency} """
    
    if not csound_imported:
        raise ImportError("Install Csound")

    score = ""
    instr = f'"{instr}"' if isinstance(instr, str) else instr
    start_time = 0
    for item in ziffers.evaluated_values:
        if isinstance(item, Chord):
            for freq, dur in zip(item.get_freq(), item.get_duration()):
                score += f"i {instr} {start_time} {dur * 4 * 60 / bpm} {amp} {freq:.2f}\n"
            start_time += max(item.get_duration()) * 4 * 60 / bpm
        elif isinstance(item, Rest):
            score += f"i {instr} {start_time} {item.get_duration() * 4 * 60 / bpm} {amp} 0\n"
        elif isinstance(item, Pitch):
            score += f"i {instr} {start_time} {item.get_duration() * 4 * 60 / bpm} {amp} {item.get_freq():.2f}\n"
            start_time += item.get_duration() * 4 * 60 / bpm
    return score

def to_music21(expression: str | Ziffers, **options):
    """Helper for passing options to the parser"""

    if not music21_imported:
        raise ImportError("Install Music21 library")

    # Register the ZiffersMusic21 converter
    converter.registerSubConverter(ZiffersMusic21)

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

            if "key" in options:
                accidentals = accidentals_from_note_name(options["key"])
            else:
                accidentals = 0

            if "scale" in options:
                scale_upper = options["scale"].upper()
                scale_lower = options["scale"].lower()
                if scale_upper in MODES:
                    accidentals += MODE_ACCIDENTALS[scale_upper]
                    note_stream.append(key.KeySignature(accidentals,mode=scale_lower))
            else:
                note_stream.append(key.KeySignature(accidentals))

            if "bpm" in options:
                note_stream.append(tempo.MetronomeMark(number=options["bpm"]))
            
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