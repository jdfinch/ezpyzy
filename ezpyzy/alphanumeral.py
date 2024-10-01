
import itertools as it


def alphanumeral(num, numerals='ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    if num < 0:
        negative = True
        num = -num
    else:
        negative = False
    result = []
    while num >= 0:
        num, remainder = divmod(num, len(numerals))
        result.append(numerals[remainder])
        if num == 0:
            break
        num -= 1
    if negative:
        result.append('-')
    return ''.join(reversed(result))


def alphanumerals(n=None, numerals='ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    for i in it.count():
        if n is not None and i == n:
            return
        yield alphanumeral(i, numerals)


if __name__ == '__main__':
    for i in range(-30, 30):
        print(f'{i} -> {alphanumeral(i)}')