"""Collection of converters"""
from ziffers import zparse, Ziffers, Pitch, Rest, Chord

try:
    from music21 import converter, note, stream, meter, chord, environment
    music21_imported: bool = True
except ImportError:
    music21_imported: bool = False

def to_music21(expression: str | Ziffers, **options):
    """Helper for passing options to the parser"""

    if not music21_imported:
        raise ImportError("Install Music21 library")

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