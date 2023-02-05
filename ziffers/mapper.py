from lark import Transformer
from .classes import *
from .common import flatten, sum_dict
from .defaults import DEFAULT_DURS
import operator


class ZiffersTransformer(Transformer):
    def start(self, items):
        return Sequence(values=items[0])

    def sequence(self, items):
        return flatten(items)

    def random_integer(self, s):
        val = s[0][1:-1].split(",")
        return RandomInteger(min=val[0], max=val[1], text=s[0].value)

    def range(self, s):
        val = s[0].split("..")
        return Range(start=val[0], end=val[1], text=s[0])

    def cycle(self, items):
        values = items[0]
        return Cyclic(values=values)

    def pc(self, s):
        if len(s) > 1:
            # Collect&sum prefixes from any order: _qee^s4 etc.
            result = sum_dict(s)
            return Pitch(**result)
        else:
            val = s[0]
            return Pitch(**val)

    def pitch(self, s):
        return {"pc": int(s[0].value), "text": s[0].value}

    def prefix(self, s):
        return s[0]

    def oct_change(self, s):
        octave = s[0]
        return [OctaveChange(oct=octave["oct"], text=octave["text"]), s[1]]

    def oct_mod(self, s):
        octave = s[0]
        return [OctaveMod(oct=octave["oct"], text=octave["text"]), s[1]]

    def escaped_octave(self, s):
        value = s[0][1:-1]
        return {"oct": int(value), "text": s[0].value}

    def octave(self, s):
        value = sum([1 if char == "^" else -1 for char in s[0].value])
        return {"oct": value, "text": s[0].value}

    def chord(self, s):
        return Chord(pcs=s, text="".join([val.text for val in s]))

    def dur_change(self, s):
        durs = s[0]
        return DurationChange(dur=durs[1], text=durs[0])

    def char_change(self, s):
        chars = ""
        durs = 0.0
        for (dchar, dots) in s:
            val = DEFAULT_DURS[dchar]
            if dots > 0:
                val = val * (2.0 - (1.0 / (2 * dots)))
            chars = chars + (dchar + "." * dots)
            durs = durs + val
        return [chars, durs]

    def dchar_not_prefix(self, s):
        dur = s[0].split(".", 1)
        dots = 0
        if len(dur) > 1:
            dots = len(dur[1]) + 1
        return [dur[0], dots]

    def escaped_decimal(self, s):
        val = s[0]
        val["text"] = "<" + val["text"] + ">"
        return val

    def random_pitch(self, s):
        return RandomPitch(text="?")

    def random_percent(self, s):
        return RandomPercent(text="%")

    def duration_chars(self, s):
        durations = [val[1] for val in s]
        characters = "".join([val[0] for val in s])
        return {"dur": sum(durations), "text": characters}

    def dotted_dur(self, s):
        key = s[0]
        val = DEFAULT_DURS[key]
        dots = len(s) - 1
        if dots > 0:
            val = val * (2.0 - (1.0 / (2 * dots)))
        return [key + "." * dots, val]

    def decimal(self, s):
        val = s[0]
        return {"dur": float(val), "text": val.value}

    def dot(self, s):
        return "."

    def dchar(self, s):
        chardur = s[0].value
        return chardur

    def WS(self, s):
        return Whitespace(text=s[0])

    def subdivision(self, items):
        values = flatten(items[0])
        return Subdivision(
            values=values, text="[" + "".join([val.text for val in values]) + "]"
        )

    def subitems(self, s):
        return s

    # Eval rules

    def eval(self, s):
        val = s[0]
        return Eval(values=val)

    def operation(self, s):
        return s

    def atom(self, s):
        val = s[0].value
        return Atom(value=val, text=val)

    # List rules

    def list(self, items):
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
        if len(items) > 2:
            prefixes = sum_dict(items[0:-2])  # If there are prefixes
            if items[-1] != None:
                seq = RepeatedListSequence(
                    values=items[-2],
                    repeats=items[-1],
                    wrap_end=":" + items[-1].text + ")",
                )
            else:
                seq = RepeatedListSequence(
                    values=items[-2], repeats=Integer(text="1", value=1)
                )
            seq.update_values(prefixes)
            return seq
        else:
            if items[-1] != None:
                seq = RepeatedListSequence(
                    values=items[-2],
                    repeats=items[-1],
                    wrap_end=":" + items[-1].text + ")",
                )
            else:
                seq = RepeatedListSequence(
                    values=items[-2], repeats=Integer(text="1", value=1)
                )
            return seq

    def SIGNED_NUMBER(self, s):
        val = s.value
        return Integer(text=val, value=int(val))

    def number(self, s):
        return s

    def cyclic_number(self, s):
        return Cyclic(values=s)

    def lisp_operation(self, s):
        op = s[0]
        values = s[1:]
        return Operation(
            operator=op,
            values=values,
            text="(+" + "".join([v.text for v in values]) + ")",
        )

    def operator(self, s):
        val = s[0].value
        return Operator(text=val)

    def list_items(self, s):
        return Sequence(values=s)

    def list_op(self, s):
        return ListOperation(values=s)

    def euclid(self, s):
        params = s[1][1:-1].split(",")
        init = {"onset": s[0], "pulses": params[0], "length": params[1]}
        text = s[0].text + s[1]
        if len(params) > 2:
            init["rotate"] = params[2]
        if len(s) > 2:
            init["offset"] = s[2]
            text = text + s[2].text
        init["text"] = text
        return Euclid(**init)

    def euclid_operator(self, s):
        return s.value

    def repeat(self, s):
        if s[-1] != None:
            return RepeatedSequence(
                values=s[0], repeats=s[-1], wrap_end=":" + s[-1].text + "]"
            )
        else:
            return RepeatedSequence(values=s[0], repeats=Integer(value=1, text="1"))
