""" Common methods used in parsing """
import re


def flatten(arr: list) -> list:
    """Flattens array"""
    return (
        flatten(arr[0]) + (flatten(arr[1:]) if len(arr) > 1 else [])
        if isinstance(arr, list)
        else [arr]
    )


def sum_dict(arr: list[dict]) -> dict:
    """Sums a list of dicts: [{a:3,b:3},{b:1}] -> {a:3,b:4}"""
    result = arr[0]
    for element in arr[1:]:
        for key in element.keys():
            if key in result:
                result[key] = result[key] + element[key]
            else:
                result[key] = element[key]
    return result


def string_rewrite(axiom: str, rules: dict):
    """String rewrite / Lindemeyer system for rule based text manipulation

    Args:
        axiom (str): Input string
        rules (dict): String manipulation rules in dict:

    Example:
        rules = {
            "1": "2",
            "[2-9]": "45",
            "4": lambda: str(randint(1, 7)),
            "([1-9])(5)": lambda a, b: str(int(a)*int(b))
        }

        for i range(10):
            print(string_rewrite("1", rules))
    """

    def _apply_rules(match):
        for key, value in rules.items():
            if re.match(key, match.group(0)):
                if callable(value):
                    yield value(
                        *match.groups()
                    ) if value.__code__.co_argcount > 0 else value()
                yield value

    pattern = re.compile("|".join(rules.keys()))
    return pattern.sub(lambda m: next(_apply_rules(m)), axiom)


def euclidian_rhythm(pulses: int, length: int, rotate: int = 0):
    """Calculate Euclidean rhythms. Original algorithm by Thomas Morrill."""

    def _starts_descent(list, index):
        length = len(list)
        next_index = (index + 1) % length
        return list[index] > list[next_index]

    def rotation(l, n):
        return l[-n:] + l[:-n]

    if pulses >= length:
        return [True]

    res_list = [pulses * t % length for t in range(-1, length - 1)]
    bool_list = [_starts_descent(res_list, index) for index in range(length)]

    return rotation(bool_list, rotate)
