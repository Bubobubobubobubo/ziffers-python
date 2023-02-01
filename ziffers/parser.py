from rich import print
from .mapper import *
from pathlib import Path
from lark import Lark

grammar_path = Path(__file__).parent
grammar = grammar_path / "ziffers.lark"

ziffers_parser = Lark.open(grammar, rel_to=__file__, start='value', parser='lalr', transformer=ZiffersTransformer())

def parse_expression(expr):
    return ziffers_parser.parse(expr)