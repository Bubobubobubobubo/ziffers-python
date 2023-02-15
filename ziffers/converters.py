"""Collection of converters"""
from music21 import converter, note, stream, meter, chord
from ziffers import zparse, Ziffers, Pitch, Rest, Chord

def to_music21(strData: str|Ziffers, **options):
    """Helper for passing options to the parser"""
    converter.registerSubconverter(ZiffersMusic21)
    
    if isinstance(strData,Ziffers):
        if options:
            options["preparsed"] = strData
        else:
            options = {"preparsed": strData}
        options = {"ziffers": options}
        return converter.parse("PREPARSED", format="ziffers", keywords=options)

    if options:
        options = {"ziffers": options}
        return converter.parse(strData, format="ziffers", keywords=options)
    else:
        test = converter.parse(strData, format="ziffers")
        return test

def set_musescore_path(path: str):
    """Helper for setting the Musescore path"""
    us = environment.UserSettings()
    # Default windows path:
    # 'C:\\Program Files\\MuseScore 3\\bin\\MuseScore3.exe'
    us['musicxmlPath'] = path
    us['musescoreDirectPNGPath'] = path

class ZiffersMusic21(converter.subConverters.SubConverter):
    """Ziffers converter to Music21"""
    registerFormats = ("ziffers",)
    registerInputExtensions = ("zf",)

    def parseData(self, strData, number=None):
        """Parses Ziffers string to Music21 object"""
        # Look for options in keywords object
        keywords = self.keywords["keywords"]
        if "ziffers" in keywords:
            options = keywords["ziffers"]
            if "preparsed" in options:
                parsed = options["preparsed"]
            else:
                parsed = zparse(strData, **options)
        else:
            parsed = zparse(strData)

        s = stream.Part()
        if "time" in options:
            m = meter.TimeSignature(options["time"])  # Common time
        else:
            m = meter.TimeSignature("c")  # Common time

        s.insert(0, m)
        for item in parsed:
            if isinstance(item,Pitch):
                m_item = note.Note(item.note)
                m_item.duration.quarterLength = item.duration * 4
            elif isinstance(item,Rest):
                m_item = note.Rest(item.duration * 4)
            elif isinstance(item,Chord):
                m_item = chord.Chord(item.notes)
                m_item.duration.quarterLength = item.duration * 4
            s.append(m_item)
        self.stream = s.makeMeasures()
