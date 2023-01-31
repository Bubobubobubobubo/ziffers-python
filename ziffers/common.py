def flatten(arr) -> list: 
    return flatten(arr[0]) + (flatten(arr[1:]) if len(arr) > 1 else []) if type(arr) is list else [arr]