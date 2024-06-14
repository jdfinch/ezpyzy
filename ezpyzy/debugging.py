
import sys


def debugging() -> bool:
    gettrace = getattr(sys, 'gettrace', None)
    if gettrace is None:
        return False
    elif gettrace():
        return True
    else:
        return False


if __name__ == '__main__':
    print('Debugging?',  debugging())