from lark import Transformer
from .classes import *
from .common import flatten
from .defaults import default_durs

class ZiffersTransformer(Transformer):
    
    def root(self, items):
        return Ziffers(flatten(items))

    def list(self,items):
        values = flatten(items[0].values)
        return Sequence(values=values,text="("+"".join([val.text for val in values])+")")

    def random_integer(self,s):
        val = s[0][1:-1].split(",")
        return RandomInteger(min=val[0],max=val[1],text=s[0])

    def range(self,s):
        val = s[0].split("..")
        return Range(start=val[0],end=val[1],text=s[0])
    
    def cycle(self, items):
        values = items[0].values
        no_spaces = [val for val in values if type(val)!=Meta]
        return Cyclic(values=no_spaces,text="<"+"".join([val.text for val in values])+">")

    def pc(self, s):
        if(len(s)>1):
            # Collect&sum prefixes from any order: _qee^s4 etc.
            result = s[0]
            for hash in s[1:]:
                for key in hash.keys():
                    if key in result:
                        result[key] = result[key] + hash[key]
                    else:
                        result[key] = hash[key]            
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
        if(dots>1):
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
        return Meta(text=s[0])

    def subdivision(self,items):
        values = flatten(items[0])
        return Subdivision(values=values,text="["+"".join([val.text for val in values])+"]")

    def subitems(self,s):
        return s
