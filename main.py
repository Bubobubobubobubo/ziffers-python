from ziffers import *
from rich import print

if __name__ == "__main__":
    expressions = {
            'Pitches': "-2 -1 0 1 2",
            'Chords': "0 024 2 246",
            'Note lengths': "w 0 h 1 q 2 e 3 s 4",
            'Subdivision': "[1 2 [3 4]]",
            'Decimal durations': "0.25 0 1 [0.333]2 3",
            'Octaves': "^ 0 ^ 1 _ 2 _ 3",
            'Escaped octave': "<2> 1 <1>1<-2>3",
            'Roman chords': "i ii iii+4 iv+5 v+8 vi+10 vii+20",
            'Named chords': "i^7 i^min i^dim i^maj7",
            'Modal interchange (a-g)': "iiia ig ivf^7",
            'Escape/eval': "{10 11} {1.2 2.43} {3+1*2}",
            'Randoms': "% ? % ? % ?",
            'Random between': "(-3,6)",
            'Random selections': "[q 1 2, q 3 e 4 6]",
            'Repeat': "[: 1 (2,6) 3 :4]",
            'Repeat cycles': "[: <q e> (1,4)  <(2 3) (3 (1,7))> :]",
            'Lists': "h 1 q(0 1 2 3) 2",
            'List cycles': "(: <q e> (1,4) <(2 3) (3 (1,7))> :)",
            'Loop cycles (for zloop or z0-z9)': "<0 <1 <2 <3 <4 5>>>>>",
            'Basic operations': "(1 2 (3 4)+2)*2 ((1 2 3)+(0 9 13))-2 ((3 4 {10})*(2 9 3))%7",
            'Product operations': "(0 1 2 3)+(1 4 2 3) (0 1 2)-(0 2 1)+2",
            'Euclid cycles': "(q1)<6,7>(q4 (e3 e4) q2) or (q1)<6,7<(q4 q3 q2)",
            'Transformations': "(0 1 2)<r> (0 1 2)<i>(-2 1)",
            'List assignation': "A=(0 (1,6) 3) B=(3 ? 2) B A B B A",
            'Random repeat': "(: 1 (2,6) 3 :4)",
            'Conditionals': "1 {%<0.5?3} 3 4 (: 1 2 {%<0.2?3:2} :3)",
            'Functions': "(0 1 2 3){x%3==0?x-2:x+2}",
            'Polynomials': "(-10..10){(x**3)*(x+1)%12}",
    }
    for expression in expressions:
        try: 
            print(f"[green]== Parsing: [yellow]{expression}[/yellow] ==[/green]")
            parse_expression(expression)
        except Exception as e:
            print(f"[red]Failed parsing {expression}[/red]: {e}")
