from lark import Transformer
from .classes import *
from .common import flatten, sum_dict
from .defaults import default_durs
import operator

class ZiffersTransformer(Transformer):
    
    def sequence(self,items):
        return Sequence(values=flatten(items))

    def random_integer(self,s):
        val = s[0][1:-1].split(",")
        return RandomInteger(min=val[0],max=val[1],text=s[0])

    def range(self,s):
        val = s[0].split("..")
        return Range(start=val[0],end=val[1],text=s[0])
    
    def cycle(self, items):
        values = items[0].values
        return Cyclic(values=values, wrapper="<>")

    def pc(self, s):
        if(len(s)>1):
            # Collect&sum prefixes from any order: _qee^s4 etc.
            result = sum_dict(s)
            return Pitch(**result)
        else:
            val = s[0]
            return Pitch(**val)    

    def pitch(self,s):
        return {"pc":int(s[0].value),"text":s[0].value}

    def prefix(self,s):
        return s[0]

    def oct_change(self,s):
        octave = s[0]
        return [OctaveChange(oct=octave["oct"],text=octave["text"]),s[1]]

    def oct_mod(self,s):
        octave = s[0]
        return [OctaveMod(oct=octave["oct"],text=octave["text"]),s[1]]

    def escaped_octave(self,s):
        value = s[0][1:-1]
        return {"oct": int(value), "text":s[0].value}

    def octave(self,s):
        value = sum([1 if char=='^' else -1 for char in s[0].value])
        return {"oct": value, "text":s[0].value}

    def chord(self,s):
        return Chord(pcs=s,text="".join([val.text for val in s]))

    def dur_change(self,s):
        duration = s[0]
        return [DurationChange(dur=duration["dur"], text=duration["text"]),s[1]]

    def escaped_decimal(self,s):
        val = s[0]
        val["text"] = "<"+val["text"]+">"
        return val

    def random_pitch(self,s):
        return RandomPitch(text="?")

    def random_percent(self,s):
        return RandomPercent(text="%")

    def duration_chars(self,s):
        durations = [val[1] for val in s]
        characters = "".join([val[0] for val in s])
        return {"dur": sum(durations), "text":characters}

    def dotted_dur(self,s):
        key = s[0]
        val = default_durs[key]
        dots = len(s)-1
        if(dots>0):
            val = val * (2.0-(1.0/(2*dots)))
        return [key+"."*dots,val]

    def decimal(self,s):
        val = s[0]
        return {"dur": float(val),"text": val.value}

    def dot(self,s):
        return "."

    def dchar(self,s):
        chardur = s[0].value
        return chardur

    def WS(self,s):
        return Item(text=s[0])

    def subdivision(self,items):
        values = flatten(items[0])
        return Subdivision(values=values,text="["+"".join([val.text for val in values])+"]")

    def subitems(self,s):
        return s

    # Eval rules

    def eval(self,s):
        val = s[0]
        return Eval(values=val,wrapper="{}")

    def operation(self,s):
        return s

    def atom(self,s):
        val = s[0].value
        return Atom(value=val,text=val)

    # List rules

    def list(self,items):
        if len(items)>1:
            prefixes = sum_dict(items[0:-1])
            seq = items[-1]
            seq.wrapper = "()"
            seq.text = prefixes["text"] + seq.text
            seq.update_values(prefixes)
            return seq
        else:
            seq = items[0]
            seq.wrapper = "()"
            return seq
    
    def SIGNED_NUMBER(self, s):
        val = s.value
        return Integer(text=val,value=int(val))

    def lisp_operation(self,s):
        op = s[0]
        values = s[1:]
        return Operation(operator=op,values=values,text="(+"+"".join([v.text for v in values])+")")

    def operator(self,s):
        val = s[0].value
        return Operator(text=val)

    def list_items(self,s):
        return Sequence(values=s)

    def list_op(self,s):
        return ListOperation(values=s)