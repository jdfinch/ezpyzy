
import itertools as it


def digital_iteration(n=None, chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    for i in it.count():
        if n is not None and i == n:
            return
        name = ''
        index = i
        while index >= 0:
            name = chars[index % 26] + name
            index //= 26
            index -= 1
        yield name


if __name__ == '__main__':
    for i, name in zip(range(100), digital_iteration("ABCDEFGHIJKLMNOPQRSTUVWXYZ")):
        print(name, end=', ')