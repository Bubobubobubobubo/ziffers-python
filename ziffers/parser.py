""" Module for the parser """
from pathlib import Path
from functools import lru_cache
from lark import Lark
from .classes.root import Ziffers
from .mapper import ZiffersTransformer


grammar_path = Path(__file__).parent
grammar_folder = Path.joinpath(grammar_path, "spec")
grammar_file = Path.joinpath(grammar_folder, "ziffers.lark")

ziffers_parser = Lark.open(
    str(grammar_file),
    rel_to=__file__,
    start="root",
    parser="lalr",
    transformer=ZiffersTransformer(),
)


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

def collect(gen: Ziffers, num: int, key: str = None) -> list:
    """Collect n-item from parsed Ziffers"""
    return list(yield_items(gen,num,key))
    