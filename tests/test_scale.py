""" Tests for the scale module """
import pytest
from ziffers import scale



@pytest.mark.parametrize(
    "name,expected",
    [
        ("C4", 60),
        ("A1", 33),
        ("Bb3", 58),
        ("C#1", 25),
        ("foo", 60),
    ],
)
def test_notenames(name: str, expected: int):
    assert scale.note_to_midi(name) == expected


@pytest.mark.parametrize(
    "pcs,expected",
    [
        (
            list(range(-9, 10)),
            [
                45,
                47,
                48,
                50,
                52,
                53,
                55,
                57,
                59,
                60,
                62,
                64,
                65,
                67,
                69,
                71,
                72,
                74,
                76,
            ],
        ),
    ],
)
def test_note_to_midi(pcs: str, expected: int):
    assert [
        scale.note_from_pc(root=60, pitch_class=val, intervals="Ionian") for val in pcs
    ] == expected
