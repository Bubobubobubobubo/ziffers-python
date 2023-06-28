# Ziffers for Python 3.10+

This repo is hosting experimental parser for the [Ziffers](https://github.com/amiika/ziffers) numbered musical notation to Python 3.10+. This library is using lark lalr-1 parser and ebnf PEG for parsing the notation.

## Supported environments

Ziffers python supports following live coding and computer-aided composition environments:

* [Sardine](https://github.com/Bubobubobubobubo/sardine)
* [Music21](https://github.com/cuthbertLab/music21)
* [Csound](http://www.csounds.com/manual/html/ScoreTop.html)
* [Sonicsynth](https://github.com/Frikallo/SonicSynth)

# Status:

**Supported:**
```
Pitches: -2 -1 0 1 2
Chords: 0 024 2 246
Note lengths: w 0 h 1 q 2 e 3 s 4
Subdivision: [1 2 [3 4]]
Decimal durations: 0.25 0 1 <0.333>2 3
Octaves: ^ 0 ^ 1 _ 2 _ 3
Escaped octave: <2> 1 <1>1<-2>3
Named chords: i i i i
Randoms: % ? % ? % ?
Random between: (-3,6)
Repeat: [: 1 (2,6) 3 :4]
Repeat cycles: [: <q e> (1,4) <(2 3) (3 (1,7))> :]
Lists: h 1 q(0 1 2 3) 2
List cycles: (: <q e> (1,4) <(2 3) (3 (1,7))> :)
Loop cycles: <0 <1 <2 <3 <4 5>>>>>
Basic operations: (1 2 (3 4)+2)*2 ((1 2 3)+(0 9 13))-2 ((3 4 10)*(2 9 3))%7
Product operations: (0 1 2 3)+(1 4 2 3) (0 1 2)-(0 2 1)+2
Euclid cycles: (q1)<6,7>(q4 (e3 e4) q2) (q1)<6,7>(q4 q3 q2)
Transformations: (0 1 2)<r> (0 1 2)<i>(-2 1)
List assignation: A=(0 (1,6) 3) B=(3 ? 2) B A B B A
Random repeat: (: 1 (2,6) 3 :4)
```

**New features:**
```
Shorthand for random repeat: (2 5):3 [2 5 1]:4 (1,6):6
```

**Partial support:**
```
Escape/eval: {10 11} {3+1*2} // {1.2 2.43} NOT SUPPORTED YET.
Roman chords: i ii iii i^maj i^7
```

**TBD:**
```
Random selections: [q 1 2, q 3 e 4 6]
Conditionals: 1 {%<0.5?3} 3 4 (: 1 2 {%<0.2?3:2} :3)
Functions: (0 1 2 3){x%3==0?x-2:x+2}
Polynomials: (-10..10){(x**3)*(x+1)%12}
Modal interchange (a-g): iiia ig ivf^7
```