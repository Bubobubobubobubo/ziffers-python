""" Module for the parser """
from pathlib import Path
from functools import lru_cache
from lark import Lark
from .classes.root import Ziffers
from .mapper import ZiffersTransformer, ScalaTransformer


grammar_path = Path(__file__).parent
grammar_folder = Path.joinpath(grammar_path, "spec")
ziffers_grammar = Path.joinpath(grammar_folder, "ziffers.lark")
scala_grammar = Path.joinpath(grammar_folder, "scala.lark")

ziffers_parser = Lark.open(
    str(ziffers_grammar),
    rel_to=__file__,
    start="root",
    parser="lalr",
    transformer=ZiffersTransformer(),
)

scala_parser = Lark.open(
    str(scala_grammar),
    rel_to=__file__,
    start="root",
    parser="lalr",
    transformer=ScalaTransformer(),
)

def parse_scala(expr: str):
    """Parse an expression using the Ziffers parser

    Args:
        expr (str): Ziffers expression as a string

    Returns:
        Ziffers: Reutrns Ziffers iterable
    """
    # Ignore everything before last comment "!"
    values = expr.split("!")[-1]
    return scala_parser.parse(values)


def parse_expression(expr: str) -> Ziffers:
    """Parse an expression using the Ziffers parser

    Args:
        expr (str): Ziffers expression as a string

    Returns:
        Ziffers: Reutrns Ziffers iterable
    """
    return ziffers_parser.parse(expr)

@lru_cache
def zparse(expr: str, **opts) -> Ziffers:
    """Parses ziffers expression with options

    Args:
        expr (str): Ziffers expression as a string
        opts (dict, optional): Options for parsing the Ziffers expression. Defaults to None.

    Returns:
        Ziffers: Returns Ziffers iterable parsed with the given options
    """
    if "scale" in opts:
        scale = opts["scale"]
        if isinstance(scale,str) and not scale.isalpha():
            parsed_scale = parse_scala(scale)
            opts["scale"] = parsed_scale

    parsed = parse_expression(expr)
    parsed.init_opts(opts)
    return parsed


# pylint: disable=invalid-name


def z(expr: str, **opts) -> Ziffers:
    """Shortened method name for zparse"""
    return zparse(expr, **opts)

def yield_items(gen: Ziffers, num: int, key: str = None) -> list:
    """Yield n items from parsed Ziffers"""
    for i in range(num):
        if key is not None:
            yield getattr(gen[i],key,None)
        else:
            yield gen[i]

def get_items(gen: Ziffers, num: int, key: str = None) -> list:
    """Get n-item from parsed Ziffers. Functional alternative to Ziffers-object collect method."""
    return list(yield_items(gen,num,key))
    