
def split(string, *separators):
    """Split a string into a list of substrings using the given separators."""
    result = [string]
    for separator in separators:
        new_result = []
        for substring in result:
            new_result.extend(substring.split(separator))
        result = new_result
    return result