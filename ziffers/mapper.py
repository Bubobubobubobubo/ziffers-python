""" Lark transformer for mapping Lark tokens to Ziffers objects """
import random
from lark import Transformer, Token
from .scale import cents_to_semitones, ratio_to_cents, monzo_to_cents
from .classes.root import Ziffers
from .classes.sequences import (
    Sequence,
    ListSequence,
    RepeatedListSequence,
    ListOperation,
    RepeatedSequence,
    Euclid,
    Subdivision,
    Eval,
    Operation,
    LispOperation,
)
from .classes.items import (
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
    Cyclic,
    RandomInteger,
    Range,
    Operator,
    Atom,
    Integer,
    VariableAssignment,
    Variable,
    VariableList,
    Measure,
)
from .common import flatten, sum_dict
from .defaults import DEFAULT_DURS, OPERATORS
from .scale import parse_roman


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
        if len(items) > 0:
            prefixes = sum_dict(items)
            text_prefix = prefixes.pop("text")
            prefixes["prefix"] = text_prefix
            return Rest(text=text_prefix + "r", local_options=prefixes)
        return Rest(text="r")

    def measure(self, items):
        """Return new measure"""
        return Measure()

    def random_integer(self, items) -> RandomInteger:
        """Parses random integer syntax"""
        if len(items) > 1:
            prefixes = sum_dict(items[0:-1])  # If there are prefixes
            text_prefix = prefixes.pop("text")
            prefixes["prefix"] = text_prefix
            val = items[-1][1:-1].split(",")
            return RandomInteger(
                min=int(val[0]),
                max=int(val[1]),
                text=text_prefix + items[-1],
                local_options=prefixes,
            )
        else:
            val = items[0][1:-1].split(",")
            return RandomInteger(min=int(val[0]), max=int(val[1]), text=items[0])

    def random_integer_re(self, items):
        """Return random integer notation from regex"""
        return items[0].value

    def range(self, items) -> Range:
        """Parses range syntax"""
        if len(items) > 1:
            prefixes = sum_dict(items[0:-1])  # If there are prefixes
            text_prefix = prefixes.pop("text")
            prefixes["prefix"] = text_prefix
            val = items[-1].split("..")
            return Range(
                start=int(val[0]),
                end=int(val[1]),
                text=text_prefix + items[-1],
                local_options=prefixes,
            )
        # Else
        val = items[0].split("..")
        return Range(start=int(val[0]), end=int(val[1]), text=items[0])

    def range_re(self, items):
        """Return range value from regex"""
        return items[0].value

    def cycle(self, items) -> Cyclic:
        """Parses cycle"""
        values = items[0]
        return Cyclic(values=values)

    def pitch_class(self, items):
        """Parses pitch class"""

        # If there are prefixes
        if len(items) > 1:
            # Collect&sum prefixes from any order: _qee^s4 etc.
            prefixes = sum_dict(items[0:-1])  # If there are prefixes
            text_prefix = prefixes.pop("text")
            prefixes["prefix"] = text_prefix
            pitch = Pitch(
                pitch_class=items[-1]["pitch_class"],
                text=text_prefix + items[-1]["text"],
                local_options=prefixes,
            )
            return pitch

        val = items[0]
        return Pitch(**val)

    def pitch(self, items):
        """Return pitch class info"""
        text_value = items[0].value.replace("T", "10").replace("E", "11")
        return {"pitch_class": int(text_value), "text": items[0].value}

    def escaped_pitch(self, items):
        """Return escaped pitch"""
        val = items[0].value[1:-1]
        return {"pitch_class": int(val), "text": val}

    def prefix(self, items):
        """Return prefix"""
        return items[0]

    def oct_change(self, items):
        """Parses octave change"""
        octave = items[0]
        return [
            OctaveChange(value=octave["octave_change"], text=octave["text"]),
            items[1],
        ]

    def oct_mod(self, items):
        """Parses octave modification"""
        octave = items[0]
        return [OctaveAdd(value=octave["octave"], text=octave["text"]), items[1]]

    def escaped_octave(self, items):
        """Return octave info"""
        value = items[0][1:-1]
        return {"octave_change": int(value), "text": items[0].value}

    def octave(self, items):
        """Return octaves ^ and _"""
        value = sum(1 if char == "^" else -1 for char in items[0].value)
        return {"octave": value, "text": items[0].value}

    def modifier(self, items):
        """Return modifiers # and b"""
        value = 1 if items[0].value == "#" else -1
        return {"modifier": value, "text": items[0].value}

    def chord(self, items):
        """Parses chord"""
        if isinstance(items[-1], Token):
            return Chord(
                pitch_classes=items[0:-1],
                text="".join([val.text for val in items[0:-1]]),
                inversions=int(items[-1].value[1:]),
            )
        return Chord(pitch_classes=items, text="".join([val.text for val in items]))

    def invert(self, items):
        """Return chord inversion"""
        return items[0]

    def named_roman(self, items) -> RomanNumeral:
        """Parse chord from roman numeral"""
        numeral = items[0].value
        # TODO: Refactor this and the rule
        if len(items) == 1:
            return RomanNumeral(value=parse_roman(numeral), text=numeral)
        if len(items) > 2:
            name = items[1]
            inversions = int(items[-1].value[1:])
            return RomanNumeral(
                text=numeral,
                value=parse_roman(numeral),
                chord_type=name,
                inversions=inversions,
            )
        elif len(items) == 2:
            if isinstance(items[-1], Token):
                inversions = int(items[-1].value[1:])
                return RomanNumeral(
                    value=parse_roman(numeral),
                    text=numeral,
                    inversions=inversions,
                )
            else:
                return RomanNumeral(
                    value=parse_roman(numeral), text=numeral, chord_type=items[1]
                )

    def chord_name(self, item):
        """Return name for chord"""
        return item[0].value

    def roman_number(self, item):
        """Return roman numeral"""
        return item[0]

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
        return Subdivision(values=values, wrap_start="[", wrap_end="]")

    def subitems(self, items):
        """Return subdivision items"""
        return items

    # Eval rules

    def eval(self, items):
        """Parse eval"""
        return Eval(values=items)

    def sub_operations(self, items):
        """Returns list of operations"""
        return Eval(values=items[0], wrap_start="(", wrap_end=")")

    def operation(self, items):
        """Return partial eval operations"""
        if isinstance(items[0], dict):
            local_opts = items[0]
            del local_opts["text"]
            return Operation(values=flatten(items[1:]), local_options=items[0])
        return Operation(values=flatten(items))

    def atom(self, token):
        """Return partial eval item"""
        val = token[0].value
        return Atom(value=val, text=str(val))

    # Variable assignment

    def assignment(self, items):
        """Creates variable assignment"""
        var = items[0]
        op = items[1]
        content = items[2]
        return VariableAssignment(
            variable=var,
            value=content,
            text=var.text + "=" + content.text,
            pre_eval=True if op == "=" else False,
        )

    def ass_op(self, items):
        """Return parsed type for assignment: = or ~"""
        return items[0].value

    def variable(self, items):
        """Return variable"""
        if len(items) > 1:
            prefixes = sum_dict(items[0:-1])
            text_prefix = prefixes.pop("text")
            return Variable(
                name=items[-1], text=text_prefix + items[-1], local_options=prefixes
            )
        return Variable(name=items[0], text=items[0])

    def variable_char(self, items):
        """Return parsed variable name"""
        return items[0].value  # Variable(name=items[0].value, text=items[0].value)

    def variablelist(self, items):
        """Return list of variables"""
        return VariableList(values=items, text="".join([item.text for item in items]))

    # List rules

    def list(self, items):
        """Parse list sequence notation, ex: (1 2 3)"""
        if len(items) > 1:
            prefixes = sum_dict(items[0:-1])
            text_prefix = prefixes.pop("text")
            prefixes["prefix"] = text_prefix
            values = items[-1]
            seq = ListSequence(
                values=values,
                wrap_start=prefixes["prefix"] + "(",
                local_options=prefixes,
            )
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
                    local_options=prefixes,
                )
            else:
                seq = RepeatedListSequence(
                    values=items[-2],
                    repeats=Integer(text="2", value=2, local_options=prefixes),
                )
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

    def integer(self, items):
        """Parses integer from single ints"""
        concatted = sum_dict(items)
        val = concatted["text"]
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
        return LispOperation(
            operator=op,
            values=values,
            text="(+" + "".join([v.text for v in values]) + ")",
        )

    def operator(self, token):
        """Parse operator"""
        val = token[0].value
        return Operator(text=val, value=OPERATORS[val])

    def list_operator(self, token):
        """Parse list operator"""
        val = token[0].value
        return Operator(text=val, value=OPERATORS[val])

    def list_items(self, items):
        """Parse sequence"""
        return Sequence(values=items)

    def list_op(self, items):
        """Parse list operation"""
        return ListOperation(values=items)

    def right_op(self, items):
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

    def repeat_item(self, items):
        """Parse repeat item syntax to sequence, ex: 1:4 (1 2 3):5"""
        return RepeatedListSequence(
            values=[items[0]],
            repeats=items[1],
            wrap_start="",
            wrap_end=":" + items[1].text,
        )


# pylint: disable=locally-disabled, unused-argument, too-many-public-methods, invalid-name, eval-used
class ScalaTransformer(Transformer):
    """Transformer for scala scales"""

    def lines(self, items):
        """Transforms cents to semitones"""
        cents = [
            ratio_to_cents(item) if isinstance(item, int) else item for item in items
        ]
        return cents_to_semitones(cents)

    def operation(self, items):
        """Get operation"""
        # Safe eval. Items are pre-parsed.
        val = eval("".join(str(item) for item in items))
        return val

    def operator(self, items):
        """Get operator"""
        return items[0].value

    def sub_operations(self, items):
        """Get sub-operation"""
        return "(" + items[0] + ")"

    def frac_ratio(self, items):
        """Get ration as fraction"""
        ratio = items[0] / items[1]
        return ratio_to_cents(ratio)

    def decimal_ratio(self, items):
        """Get ratio as decimal"""
        ratio = float(str(items[0]) + "." + str(items[1]))
        return ratio_to_cents(ratio)

    def monzo(self, items):
        """Get monzo ratio"""
        return monzo_to_cents(items)

    def edo_ratio(self, items):
        """Get EDO ratio"""
        ratio = pow(2, items[0] / items[1])
        return ratio_to_cents(ratio)

    def edji_ratio(self, items):
        """Get EDJI ratio"""
        if len(items) > 3:
            power = items[2] / items[3]
        else:
            power = items[2]
        ratio = pow(power, items[0] / items[1])
        return ratio_to_cents(ratio)

    def int(self, items):
        """Get integer"""
        return int(items[0].value)

    def float(self, items):
        """Get float"""
        return float(items[0].value)

    def random_int(self, items):
        """Get random integer"""

        def _rand_between(start, end):
            return random.randint(min(start, end), max(start, end))

        start = items[0]
        end = items[1]
        rand_val = _rand_between(start, end)
        return rand_val

    def random_decimal(self, items):
        """Get random decimal"""

        def _rand_between(start, end):
            return random.uniform(min(start, end), max(start, end))

        start = items[0]
        end = items[1]
        rand_val = _rand_between(start, end)
        return rand_val
