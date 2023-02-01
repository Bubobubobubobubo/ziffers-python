from ziffers import *
import pytest

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
            result = parse_expression(expression)
            results.append(True)
        except Exception as e:
            print(e)
            results.append(False)

    # Return true if all the results are true (succesfully parsed)
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
    assert parse_expression(pattern).text == pattern

@pytest.mark.parametrize(
    "pattern,expected",
    [
        ("1 2 3", [1,2,3]),
        ("q2 eq3", [2,3]),
    ],
)
def test_pcs(pattern: str, expected: list):
    assert parse_expression(pattern).pcs == expected