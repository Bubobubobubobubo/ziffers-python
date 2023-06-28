"""Example of using ziffers with Csound score."""
try:
    import ctcsound
except (ImportError,TypeError):
    csound_imported = false
    
from ziffers import *

# Csound numeric score is very versatile so it is hard to do generic tranformer
# See http://www.csounds.com/manual/html/ScoreTop.html and http://www.csounds.com/manual/html/ScoreStatements.html

# There is a simple converter implemented that uses format:
# i {instrument} {start time} {duration} {amplitude} {frequency}
# See ziffers_to_csound_score in ziffers/converters.py

if(csound_imported):

    # Parse ziffers notation, scale in SCALA format
    parsed = zparse("w 0 024 q 0 1 2 346 r e (5 3 9 2 -605)+(0 -3 6) q 0h24e67s9^s1^e3^5^7", key="D4", scale="100. 200. 250. 400. 560.")

    score = ziffers_to_csound_score(parsed, 180, 1500, "FooBar") # 180 bpm, 1500 amplitude, FooBar instrument

    print("Generated score:")
    print(score)

    # Define FooBar Csound instrument
    orc = """
    instr FooBar
        out(linen(oscili(p4,p5),0.1,p3,0.1))
    endin
    """

    # Run score with Csound
    c = ctcsound.Csound()
    c.setOption("-odac")
    c.compileOrc(orc)
    c.readScore(score)
    c.start()                               
    c.perform() 
    c.stop()
else:
    print("Csound not found! First download from https://csound.com/ and add to PATH or PYENV (Windows path: C:\Program Files\Csound6_x64\bin). Then install ctcsound with 'pip install ctcsound'.")