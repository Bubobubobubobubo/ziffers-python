""" Lark transformer for mapping Lark tokens to Ziffers objects """
from typing import Optional
from lark import Transformer
from .classes import (
    Ziffers,
    Whitespace,
    DurationChange,
    OctaveChange,
    OctaveAdd,
    Pitch,
    Rest,
    RandomPitch,
    RandomPercent,
    Chord,
    RomanNumeral,
    Sequence,
    ListSequence,
    RepeatedListSequence,
    Subdivision,
    Cyclic,
    RandomInteger,
    Range,
    Operator,
    ListOperation,
    Operation,
    Eval,
    Atom,
    Integer,
    Euclid,
    RepeatedSequence,
    VariableAssignment,
    Variable
)
from .common import flatten, sum_dict
from .defaults import DEFAULT_DURS, OPERATORS
from .scale import parse_roman, chord_from_roman_numeral


# pylint: disable=locally-disabled, unused-argument, too-many-public-methods, invalid-name
class ZiffersTransformer(Transformer):
    """Rules for transforming Ziffers expressions into tree."""

    def start(self, items) -> Ziffers:
        """Root for the rules"""
        return Ziffers(values=items[0], options={})

    def sequence(self, items):
        """Flatten sequence"""
        return flatten(items)

    def rest(self, items):
        """Return duration event"""
        if len(items)>0:
            chars = items[0]
            val = DEFAULT_DURS[chars[0]]
            # TODO: Add support for dots
            #if len(chars)>1:
            #    dots = len(chars)-1
            #    val = val * (2.0 - (1.0 / (2 * dots)))
            return Rest(text=chars+"r", duration=val)
        return Rest(text="r")

        return Rest(text=chars+"r", duration=val)

    def rest_duration(self,items):
        return items[0].value

    def random_integer(self, item) -> RandomInteger:
        """Parses random integer syntax"""
        val = item[0][1:-1].split(",")
        return RandomInteger(min=int(val[0]), max=int(val[1]), text=item[0].value)

    def range(self, item) -> Range:
        """Parses range syntax"""
        val = item[0].split("..")
        return Range(start=int(val[0]), end=int(val[1]), text=item[0].value)

    def cycle(self, items) -> Cyclic:
        """Parses cycle"""
        values = items[0]
        return Cyclic(values=values)

    def pitch_class(self, item):
        """Parses pitch class"""

        # If there are prefixes
        if len(item) > 1:
            # Collect&sum prefixes from any order: _qee^s4 etc.
            result = sum_dict(item)
            return Pitch(**result)

        val = item[0]
        return Pitch(**val)

    def pitch(self, items):
        """Return pitch class info"""
        text_value = items[0].value.replace("T","10").replace("E","11")
        return {"pitch_class": int(text_value), "text": items[0].value}

    def prefix(self, items):
        """Return prefix"""
        return items[0]

    def oct_change(self, items):
        """Parses octave change"""
        octave = items[0]
        return [OctaveChange(value=octave["octave"], text=octave["text"]), items[1]]

    def oct_mod(self, items):
        """Parses octave modification"""
        octave = items[0]
        return [OctaveAdd(value=octave["octave"], text=octave["text"]), items[1]]

    def escaped_octave(self, items):
        """Return octave info"""
        value = items[0][1:-1]
        return {"octave": int(value), "text": items[0].value}

    def octave(self, items):
        """Return octaves ^ and _"""
        value = sum(1 if char == "^" else -1 for char in items[0].value)
        return {"octave": value, "text": items[0].value}

    def modifier(self, items):
        """Return modifiers # and b"""
        value = 1 if items[0].value == "#" else -1
        return {"modifier": value}

    def chord(self, items):
        """Parses chord"""
        return Chord(pitch_classes=items, text="".join([val.text for val in items]))

    def named_roman(self, items) -> RomanNumeral:
        """Parse chord from roman numeral"""
        numeral = items[0].value
        if len(items) > 1:
            name = items[1]
            chord_notes = chord_from_roman_numeral(numeral, name)
            parsed_number = parse_roman(numeral)
            return RomanNumeral(
                text=numeral, value=parsed_number, chord_type=name, notes=chord_notes
            )
        return RomanNumeral(
            value=parse_roman(numeral),
            text=numeral,
            notes=chord_from_roman_numeral(numeral),
        )

    def chord_name(self, item):
        """Return name for chord"""
        return item[0].value

    def roman_number(self, item):
        """Return roman numeral"""
        return item.value

    def dur_change(self, items):
        """Parses duration change"""
        durs = items[0]
        return DurationChange(value=durs["duration"], text=durs["text"])

    def char_change(self, items):
        """Return partial duration char info"""
        chars = ""
        durs = 0.0
        for dchar, dots in items:
            val = DEFAULT_DURS[dchar]
            if dots > 0:
                val = val * (2.0 - (1.0 / (2 * dots)))
            chars = chars + (dchar + "." * dots)
            durs = durs + val
        return {"text": chars, "duration": durs}

    def dchar_not_prefix(self, items):
        """Return partial duration char info"""
        dur = items[0].split(".", 1)
        dots = 0
        if len(dur) > 1:
            dots = len(dur[1]) + 1
        return [dur[0], dots]

    def escaped_decimal(self, items):
        """Return partial decimal info"""
        val = items[0]
        val["text"] = "<" + val["text"] + ">"
        return val

    def random_pitch(self, items):
        """Parses random pitch"""
        return RandomPitch(text="?")

    def random_percent(self, items):
        """Parses random percent"""
        return RandomPercent(text="%")

    def duration_chars(self, items):
        """Return partial duration info"""
        durations = [val[1] for val in items]
        characters = "".join([val[0] for val in items])
        return {"duration": sum(durations), "text": characters}

    def dotted_dur(self, items):
        """Return partial duration info"""
        key = items[0]
        val = DEFAULT_DURS[key]
        dots = len(items) - 1
        if dots > 0:
            val = val * (2.0 - (1.0 / (2 * dots)))
        return [key + "." * dots, val]

    def decimal(self, items):
        """Return partial duration info"""
        val = items[0]
        return {"duration": float(val), "text": val.value}

    def dot(self, items):
        """Return partial duration info"""
        return "."

    def dchar(self, items):
        """Return partial duration info"""
        chardur = items[0].value
        return chardur

    def WS(self, items):
        """Parse whitespace"""
        return Whitespace(text=items[0])

    def subdivision(self, items):
        """Parse subdivision"""
        values = flatten(items[0])
        return Subdivision(
            values=values, text="[" + "".join([val.text for val in values]) + "]"
        )

    def subitems(self, items):
        """Return subdivision items"""
        return items

    # Eval rules

    def eval(self, items):
        """Parse eval"""
        val = items[0]
        return Eval(values=val)

    def sub_operations(self, items):
        """Returns list of operations"""
        return Eval(values=items[0], wrap_start="(", wrap_end=")")

    def operation(self, items):
        """Return partial eval operations"""
        return flatten(items)

    def atom(self, token):
        """Return partial eval item"""
        val = token[0].value
        return Atom(value=val, text=val)


    # Variable assignment

    def assignment(self, items):
        var = items[0]
        content = items[1]
        return VariableAssignment(variable=var, value=content, text=var.text+"="+content.text)

    def variable(self, items):
        return Variable(name=items[0].value, text=items[0].value)

    # List rules

    def list(self, items):
        """Parse list sequence notation, ex: (1 2 3)"""
        if len(items) > 1:
            prefixes = sum_dict(items[0:-1])
            values = items[-1]
            seq = ListSequence(values=values, wrap_start=prefixes["text"] + "(")
            seq.update_values(prefixes)
            return seq
        else:
            seq = ListSequence(values=items[0])
            return seq

    def repeated_list(self, items):
        """Parse repeated list notation ex: (: 1 2 3 :)"""
        if len(items) > 2:
            prefixes = sum_dict(items[0:-2])  # If there are prefixes
            if items[-1] is not None:
                seq = RepeatedListSequence(
                    values=items[-2],
                    repeats=items[-1],
                    wrap_end=":" + items[-1].text + ")",
                )
            else:
                seq = RepeatedListSequence(
                    values=items[-2], repeats=Integer(text="2", value=2)
                )
            seq.update_values(prefixes)
            return seq
        else:
            if items[-1] is not None:
                seq = RepeatedListSequence(
                    values=items[-2],
                    repeats=items[-1],
                    wrap_end=":" + items[-1].text + ")",
                )
            else:
                seq = RepeatedListSequence(
                    values=items[-2], repeats=Integer(text="2", value=2)
                )
            return seq

    def NUMBER(self, token):
        """Parse integer"""
        val = token.value
        return Integer(text=val, value=int(val))

    def number(self, item):
        """Return partial number (Integer or RandomInteger)"""
        return item[0]

    def cyclic_number(self, item):
        """Parse cyclic notation"""
        return Cyclic(values=item)

    def lisp_operation(self, items):
        """Parse lisp like list operation"""
        op = items[0]
        values = items[1:]
        return Operation(
            operator=op,
            values=values,
            text="(+" + "".join([v.text for v in values]) + ")",
        )

    def operator(self, token):
        """Parse operator"""
        val = token[0].value
        return Operator(text=val, value=OPERATORS[val])

    def list_items(self, items):
        """Parse sequence"""
        return Sequence(values=items)

    def list_op(self, items):
        """Parse list operation"""
        return ListOperation(values=items)

    def right_op(self,items):
        """Get right value for the operation"""
        return items[0]

    def euclid(self, items):
        """Parse euclid notation"""
        params = items[1][1:-1].split(",")
        init = {"onset": items[0], "pulses": int(params[0]), "length": int(params[1])}
        text = items[0].text + items[1]
        if len(params) > 2:
            init["rotate"] = int(params[2])
        if len(items) > 2:
            init["offset"] = items[2]
            text = text + items[2].text
        init["text"] = text
        return Euclid(**init)

    def euclid_operator(self, token):
        """Return euclid operators"""
        return token.value

    def repeat(self, items):
        """Parse repeated sequence, ex: [: 1 2 3 :]"""
        if items[-1] is not None:
            return RepeatedSequence(
                values=items[0], repeats=items[-1], wrap_end=":" + items[-1].text + "]"
            )
        else:
            return RepeatedSequence(values=items[0], repeats=Integer(value=2, text="2"))
