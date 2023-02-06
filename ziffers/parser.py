from rich import print
from .mapper import *
from pathlib import Path
from lark import Lark

grammar_path = Path(__file__).parent
grammar = grammar_path / "ziffers.lark"

ziffers_parser = Lark.open(
    grammar,
    rel_to=__file__,
    start="root",
    parser="lalr",
    transformer=ZiffersTransformer(),
)

def parse_expression(expr: str):
    """Parse an expression using the Ziffers parser"""
    return ziffers_parser.parse(expr)

def zparse(expr: str, opts: dict=None):
    parsed = parse_expression(expr)
    if opts:
        parsed.set_defaults(opts)
    return parsed

def z0(expr: str, opts: dict=None):
    return zparse(expr,opts)

def z1(expr: str, opts: dict=None):
    return zparse(expr,opts)
    
def z2(expr: str, opts: dict=None):
    return zparse(expr,opts)
    
def z3(expr: str, opts: dict=None):
    return zparse(expr,opts)

def z3(expr: str, opts: dict=None):
    return zparse(expr,opts)

def z4(expr: str, opts: dict=None):
    return zparse(expr,opts)

def z5(expr: str, opts: dict=None):
    return zparse(expr,opts)

def z6(expr: str, opts: dict=None):
    return zparse(expr,opts)

def z7(expr: str, opts: dict=None):
    return zparse(expr,opts)

def z8(expr: str, opts: dict=None):
    return zparse(expr,opts)

def z9(expr: str, opts: dict=None):
    return zparse(expr,opts)