try:
    import ctcsound
except (ImportError,TypeError):
    csound_imported = false
    
from ziffers import *

if(csound_imported):

    # Parse ziffers notation
    parsed = zparse("w 0 1 q 0 1 2 3 r e 5 3 9 2 q r 0")

    # Convert to csound score
    score = to_csound_score(parsed, 180, 1500, "Meep")
    
    # Outputs: i {instrument} {start time} {duration} {amplitude} {pitch}
    print(score)

    orc = """
    instr Meep
        out(linen(oscili(p4,p5),0.1,p3,0.1))
    endin
    """

    c = ctcsound.Csound()
    c.setOption("-odac")  # Using SetOption() to configure Csound

    c.compileOrc(orc)

    c.readScore(score)
      
    c.start()                               
    c.perform() 
    c.stop()
else:
    print("Csound not found! First download from https://csound.com/ and add to PATH or PYENV (Windows path: C:\Program Files\Csound6_x64\bin). Then install ctcsound with 'pip install ctcsound'.")