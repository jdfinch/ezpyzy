
from __future__ import annotations

import re


float_grammar = '(?P<float>' + '|'.join('(?:' + x + ')' for x in [
    r'''[+-]?\d+\.\d*(?:[eE][+-]?\d+)?''',
    r'''[+-]?\d*\.\d+(?:[eE][+-]?\d+)?''',
]) + ')'
int_grammar = '(?P<int>' + '|'.join('(?:' + x + ')' for x in [
    r'''[+-]?\d+''',
]) + ')'
literal_grammar = '(?P<bool>' + '|'.join('(?:' + x + ')' for x in [
    r'''True''',
    r'''False''',
    r'''None'''
]) + ')'
str_grammar = '(?P<str>' + '|'.join('(?:' + x + ')' for x in [
    r'''"(?:[^"]|\\")*"(?!")''',
    r'''\'(?:[^\']|\\\')*\'(?!')'''
]) + ')'


tick_parser = re.compile(r'`((?:[^`]|``)*)`(?!`)')

class EosEncoder:

    def encode(self, o):
        return ...


class EosDecoder:

    def decode(self, s):
        stack = [[]]
        if not s:
            return None
        if s[0] in '-+.0123456789':
            return float(s) if '.' in s else int(s)
        elif s[0] == '[':
            children = []

        elif s[0] == '{':
            ...
        elif s[0] == '(':
            ...
        elif s[0] == '`':
            return s[1:-1].replace('``', '`')
        elif s[:4] == 'None':
            return None
        elif s[:4] == 'True':
            return True
        elif s[:5] == 'False':
            return False
        else:
            return s
        return stack[0]


if __name__ == '__main__':
    def main():

        print(-33.2E-22)

    main()