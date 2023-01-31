import pytest
from ziffers import *

@pytest.mark.parametrize(
    "pattern",
    [
        "1 2 3",
        "(1 (2 3))"
        "q 2 q2 eq.4"
    ],
)
def test_list_arithmetic(pattern: str):
    assert parse_expression(pattern).text == pattern