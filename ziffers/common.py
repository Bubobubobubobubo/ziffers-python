def flatten(arr: list) -> list:
    """Flattens array"""
    return (
        flatten(arr[0]) + (flatten(arr[1:]) if len(arr) > 1 else [])
        if isinstance(arr, list) else [arr]
    )


def sum_dict(arr: list[dict]) -> dict:
    """Sums a list of dicts: [{a:3,b:3},{b:1}] -> {a:3,b:4}"""
    result = arr[0]
    for element in arr[1:]:
        for key in hash.keys():
            if key in result:
                result[key] = result[key] + element[key]
            else:
                result[key] = element[key]
    return result
