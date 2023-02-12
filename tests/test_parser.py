""" Test cases for the parser """
import pytest
from ziffers import zparse


def test_can_parse():
    expressions = [
        "[1 [2 3]]",
        "(1 (1,3) 1..3)",
        "_^ q _qe^3 qww_4 _123 <1 2>",
        "q _2 _ 3 ^ 343",
        "2 qe2 e4",
        "q 2 <3 343>",
        "q (2 <3 343 (3 4)>)",
    ]
    results = []
    for expression in expressions:
        try:
            print(f"Parsing expression: {expression}")
            result = zparse(expression)
            results.append(True)
        except Exception as e:
            print(e)
            results.append(False)

    # Return true if all the results are true (succesfully parsed)
    print(results)
    assert all(results)


@pytest.mark.parametrize(
    "pattern",
    [
        "1 2 3",
        "q3 e4 s5",
    ],
)
def test_parsing_text(pattern: str):
    assert zparse(pattern).text == pattern


@pytest.mark.parametrize(
    "pattern,expected",
    [
        ("1 2 3", [1, 2, 3]),
        ("q2 eq3", [2, 3]),
    ],
)
def test_pitch_classes(pattern: str, expected: list):
    assert zparse(pattern).pitch_classes() == expected

# TODO: Add tests for octaves
#        ("__6 _0 _1 _2 _3 _4 _5 _6 0 1 2 3 4 5 6 ^0 ^1 ^2 ^3 ^4 ^5 ^6 ^^0", [-2, -1, -1, -1, -1, -1, -1, -1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2]),
#        ("_ 1 _2 <3>3 ^^4", [-1,-2,3,-1]),
