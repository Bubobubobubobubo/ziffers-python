def flatten(arr) -> list:
    """Flattens array"""
    return (
        flatten(arr[0]) + (flatten(arr[1:]) if len(arr) > 1 else [])
        if type(arr) is list
        else [arr]
    )


def sum_dict(arr) -> dict:
    """Sums array of dicts: [{a:3,b:3},{b:1}] -> {a:3,b:4}"""
    result = arr[0]
    for hash in arr[1:]:
        for key in hash.keys():
            if key in result:
                result[key] = result[key] + hash[key]
            else:
                result[key] = hash[key]
    return result
