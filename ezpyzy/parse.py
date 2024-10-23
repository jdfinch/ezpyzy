"""
Parser generator using a backtracking recursive descent algorithm.

Todo:
    1) Grammar specification API
    2) Tree transformer
    3) Inherit-and-init-based API with tree transformer included after parse as parse.tree
    4) Automatic regular expression group inclusion in tree
"""



from __future__ import annotations

import re
import dataclasses as dc


@dc.dataclass
class ParseTree:
    string: str = None
    start: int = 0
    end: int = 0
    children: list[ParseTree] = dc.field(default_factory=list)
    parent: ParseTree | None = None
    rule: Grammar | None = None
    option: int = 0
    index: int = 0
    leaf: bool = False

    def __iter__(self):
        return iter(self.children)

    def __getitem__(self, i):
        return self.children[i]

    def __len__(self):
        return len(self.children)

    @property
    def pattern(self):
        return self.rule[self.option][self.index]

    @property
    def span(self):
        return self.string[self.start:self.end]

    def __str__(self):
        if self.leaf:
            return f"{self.rule.name}(pattern={self.pattern}, span={self.span})"
        else:
            return f"{self.rule.name}({', '.join(str(x) for x in self.children)})"
    __repr__ = __str__


class Grammar:
    def __init__(self, name: str, *options: list[Pattern]):
        self.name = name
        self.options = list(options)

    def __iter__(self):
        return iter(self.options)

    def __getitem__(self, i):
        return self.options[i]

    def __len__(self):
        return len(self.options)

    def __str__(self):
        return f"{self.name}({' | '.join(' '.join(str(y) for y in x) for x in self.options)})"
    __repr__ = __str__



class Pattern:
    def __init__(self, pattern: str | re.Pattern | Grammar, kleenes: bool = False):
        self.pattern = re.compile(pattern) if isinstance(pattern, str) else pattern
        self.kleenes = kleenes

    def __str__(self):
        pattern = self.pattern.pattern if isinstance(self.pattern, re.Pattern) else f"Rule({self.pattern.name})"
        return f"{pattern}" if not self.kleenes else f"*{pattern}"
    __repr__ = __str__


@dc.dataclass
class Parse:
    grammar: Grammar
    string: str
    i: int = 0
    tree: ParseTree = dc.field(default_factory=ParseTree)
    node: ParseTree = None

    def __post_init__(self):
        self.node = self.tree
        self.node.rule = self.grammar

    @property
    def remaining(self):
        return self.string[self.i:]

    @property
    def rule(self):
        return self.node.rule

    @property
    def option(self):
        return self.node.option

    @property
    def index(self):
        return self.node.index

    @property
    def pattern(self):
        return self.node.rule[self.node.option][self.node.index]

    def parse(self):
        while self.i != len(self.string):
            pattern = self.pattern.pattern
            if isinstance(pattern, Grammar):
                new_node = ParseTree(self.string,
                    start=self.i, end=self.i, parent=self.node, rule=pattern, option=0, index=0)
                self.node.children.append(new_node)
                self.node = new_node
            else:
                match = pattern.match(self.remaining)
                if match:
                    end = self.i + match.end()
                    new_node = ParseTree(self.string, start=self.i, end=end, parent=self.node,
                        rule=self.rule, option=self.option, index=self.index, leaf=True)
                    self.node.children.append(new_node)
                    self.node.end = end
                    self.i = end
                    while not self.pattern.kleenes:
                        self.node.index += 1
                        self.node.end = end
                        if self.node.index >= len(self.node.rule[self.node.option]):
                            self.node = self.node.parent
                            if self.node is None:
                                if self.i != len(self.string):
                                    return None
                                else:
                                    return self.tree
                        else: break
                else:
                    while not self.pattern.kleenes: # prune tree and move to next option
                        self.node.children = []
                        self.node.index = 0
                        self.node.option += 1
                        self.i = self.node.start
                        if self.node.option >= len(self.node.rule):
                            self.node = self.node.parent
                            if self.node is None:
                                return None
                        else: break
                    else: # advance token_ids
                        self.node.children.pop()
                        while True:
                            self.node.index += 1
                            if self.node.index >= len(self.node.rule[self.node.option]):
                                self.node = self.node.parent
                                if self.node is None:
                                    if self.i != len(self.string):
                                        return None
                                    else:
                                        return self.tree
                                elif self.pattern.kleenes: break
                            else: break
        return None





if __name__ == '__main__':

    expression = Grammar('expression')
    parenthetical = Grammar('parenthetical')
    sequence = Grammar('token_ids')
    value = Grammar('value', [Pattern(r'[^()\[\],]+')])

    expression.options.extend((
        [Pattern(r'\s*'), Pattern(parenthetical), Pattern(r'\s*')],
        [Pattern(r'\s*'), Pattern(sequence), Pattern(r'\s*')],
        [Pattern(r'\s*'), Pattern(value), Pattern(r'\s*')],
    ))
    parenthetical.options.extend((
        [Pattern(r'\('), Pattern(expression), Pattern(r'\)')],
    ))
    sequence.options.extend((
        [Pattern(r'\['), Pattern(expression, kleenes=True), Pattern(r']')],
    ))

    string = '''
    [This is a (little) test [of (my) parser].]
    '''

    def main():
        parse = Parse(expression, string, tree=ParseTree(string))
        tree = parse.parse()
        print(tree)

    main()




