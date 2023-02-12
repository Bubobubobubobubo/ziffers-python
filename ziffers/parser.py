""" Module for the parser """
from pathlib import Path
from lark import Lark
from .classes import Ziffers
from .mapper import ZiffersTransformer


grammar_path = Path(__file__).parent
grammar = grammar_path / "ziffers.lark"

ziffers_parser = Lark.open(
    grammar,
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
