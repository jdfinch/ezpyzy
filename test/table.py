
from __future__ import annotations
import typing as T

import ezpyzy as ez
import dataclasses as dc


with ez.test('define'):

    @dc.dataclass
    class Turn(ez.Row):
        text: ez.Col[str, Turn]
        index: ez.Col[int, Turn] = 0
        dial: ez.Col[str, Turn] = None
        doms: ez.Col[set[str], Turn] = ez.default(set)
        id: ez.Col[str, Turn] = None

    print(f'{Turn = }')
    print(f'{Turn.__cols__ = }')
    assert list(Turn.__cols__) == ['text', 'index', 'dial', 'doms', 'id']


with ez.test('construct table'):
    turns = Turn.s((
        turn_0 := Turn('Hello', 0, 'd', {'a', 'b'}, 'xa'),
        turn_1 := Turn('world!', 1, 'd', {'c', 'd'}, 'xb'),
        turn_2 := Turn('Goodbye', 2, 'd', {'e', 'f'}, 'xc'),
        turn_3 := Turn('!!!!!!!!', 3, 'd', {'a', 'd'}, 'xd'),
    ))
    print(f'{turns = }')
    print(f'{turns.text = }')
    assert list(turns.text) == ['Hello', 'world!', 'Goodbye', '!!!!!!!!']


with ez.test('iterate over rows'):
    expected_ids = ['xa', 'xb', 'xc', 'xd']
    for turn, expected_id in zip(turns, expected_ids):
        assert expected_id == turn.id


with ez.test('construct column'):
    column = ez.Column([1, 2, 3, 6], name='numbers')
    assert list(column) == [1, 2, 3, 6]
    assert column().table.numbers is column


with ez.test('row equality'):
    assert Turn("hello", 0) == Turn("hello", 0)
    assert Turn("hello", 0) != Turn("hello", 1)


with ez.test('table equality'):
    other = Turn.s((
        other_0 := Turn('Hello', 0, 'd', {'a', 'b'}, 'xa'),
        other_1 := Turn('world!', 1, 'd', {'c', 'd'}, 'xb'),
        other_2 := Turn('Goodbye', 2, 'd', {'e', 'a'}, 'xc'),
        other_3 := Turn('!!!!!!!!', 3, 'd', {'a', 'd'}, 'xd'),
    ))
    assert turns == other


with ez.test('select a row'):
    print(f'{turns[0] = }')
    assert turns[0] is turn_0
    print(f'{turns[1] = }')
    assert turns[1] is turn_1


with ez.test('select a slice of rows'):
    print(f'{turns[1:] = }')
    assert turns[1:] == Turn.s((turn_1, turn_2))
    print(f'{turns[:2] = }')
    assert turns[:2] == Turn.s((turn_0, turn_1))


with ez.test('select rows by index'):
    print(f'{turns[[0, 2, 3]].id = }')
    assert list(turns[[0, 2, 3]].id) == ['xa', 'xc', 'xd']


with ez.test('select rows by mask'):
    assert turns[[True, False, True, False]].id == ez.Column(('xa', 'xc'))


with ez.test('select rows by predicate'):
    has_domain_a = lambda turn: 'a' in turn.doms
    assert turns[has_domain_a].id == ez.Column(('xa', 'xd'))


with ez.test('select columns'):
    selection = turns[turns.id, turns.index]
    assert list(selection()) == [turns.id, turns.index]
    assert not hasattr(selection, 'text')
    assert selection.id == ez.Column(('xa', 'xb', 'xc', 'xd'))


with ez.test('select rows and columns'):
    selection = turns[[1, 2], turns.id, turns.index]
    assert list(selection()) == [selection.id, selection.index]
    assert not hasattr(selection, 'text')
    assert selection.id == ez.Column(('xb', 'xc'))

