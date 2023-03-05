""" Test cases for the parser """
import pytest
from ziffers import zparse

@pytest.mark.parametrize(
    "pattern,expected",
    [
        ("1 2 3", [[1, 2, 3], [0.25,0.25,0.25]]),
        ("q2 eq3 e.4", [[2, 3, 4], [0.25,0.375,0.1875]]),
    ],
)
def test_multi_var(pattern: str, expected: list):
    assert zparse(pattern).collect(6, keys=["pitch_class", "duration"]) == [item*2 for item in expected]