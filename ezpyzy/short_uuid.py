"""
Short UUIDs (12 chars by default).

Has reasonably low collision probability, but collisions are still possible.

A rule of thumb is to only use this (12-char uuid) when the number of uuids you need in the collection is less than a billion, 1,000,000,000.
"""

import uuid
import sys

alphabet = '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz_'
length = 12

def encode(number, alphabet=alphabet):
    """Encode a number in Base X

    `number` is the number to encode
    `alphabet` is the character set to use
    """
    if number == 0:
        return alphabet[0]
    base = len(alphabet)
    digits = []
    while number:
        number, remainder = divmod(number, base)
        digits.append(alphabet[remainder])
    return ''.join(reversed(digits))

def short_uuid(length=length):
    """Generate a UUID from a number."""
    return encode(uuid.uuid4().int)[:length]


if __name__ == '__main__':
    x = short_uuid()
    # print(f"{len(alphabet)=}")
    print(x)
    # print(f"{len(x)=}")
    # print(f"{sys.getsizeof(x)=}")
    # print(f"{sys.getsizeof('')=}")
    # print(f"{sys.getsizeof(str(uuid.uuid4()))=}")