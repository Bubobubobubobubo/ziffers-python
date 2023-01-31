from rich import print
from .mapper import *
from pathlib import Path
from lark import Lark

grammar_path = Path(__file__).parent
grammar = grammar_path / "ziffers.lark"

ziffers_parser = Lark.open(grammar, rel_to=__file__, start='value', parser='lalr', transformer=ZiffersTransformer())

def parse_expression(expr):
    return ziffers_parser.parse(expr)

if __name__ == '__main__':
    print(ziffers_parser.parse("[1 [2 3]]"))
    #print(ziffers_parser.parse("(1 (1,3) 1..3)"))
    #print(ziffers_parser.parse("_^ q _qe^3 qww_4 _123 <1 2>"))
    #print(ziffers_parser.parse("q _2 _ 3 ^ 343"))
    #print(ziffers_parser.parse("2 qe2 e4").values)
    #print(ziffers_parser.parse("q 2 <3 343>"))
    #print(ziffers_parser.parse("q (2 <3 343 (3 4)>)"))
