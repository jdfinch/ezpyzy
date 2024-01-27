
import ezpyzy.table as ez
import dataclasses as dc
import pytest
import typing as T

ColStr = T.Union[ez.Column[str], str, None]
ColInt = T.Union[ez.Column[int], int, None]
ColBool = T.Union[ez.Column[bool], bool, None]
ColFloat = T.Union[ez.Column[float], float, None]
ColID = T.Union[ez.IDColumn[str], str, None]



@dc.dataclass
class Turn(ez.Table):
    text:ColStr = None
    speaker:ColStr = None
    dialogue:ColStr = None
    index:ColInt = None
    id:ColID = None

@dc.dataclass
class Dialogue(ez.Table):
    id:ColID = None
    sys:ColStr = None
    text:ColStr = None

def test_create_record():
    turn = Turn("Hello, how are you?", dialogue='a')
    assert turn.text() == "Hello, how are you?"
    assert turn.speaker() is None
    assert turn.dialogue() == 'a'
    assert turn.id() # a uuid with a buncha chars
    assert len(set(turn.id())) > 3

def test_table_of_records():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1]
    ])
    assert list(turns.text) == [
        "Hello my name is Sam, how are you?",
        "I'm okay, you?"
    ]
    assert list(turns.speaker) == ["Sam", "Alex"]

def test_table_of_record_dicts():
    turns = Turn.of([
        dict(text="Hello my name is Sam.", speaker="Sam", dialogue="d1", index=0),
        dict(text="I'm Alex, how are you?", speaker="Alex", dialogue="d1", index=1)
    ])
    assert list(turns.text) == [
        "Hello my name is Sam.",
        "I'm Alex, how are you?"
    ]
    assert list(turns.speaker) == ["Sam", "Alex"]

def test_table_of_columns():
    turns = Turn(
        text=ez.Column([
            "Hello my name is Sam, how are you?",
            "I'm okay, you?"
        ]),
        speaker=ez.Column([
            "Sam",
            "Alex"
        ]),
        index=ez.Column([
            0,
            1
        ])
    )
    assert list(turns.text) == [
        "Hello my name is Sam, how are you?",
        "I'm okay, you?"
    ]
    assert list(turns.speaker) == ["Sam", "Alex"]

def test_record_attributes():
    turn = Turn(
        speaker="Sam",
        dialogue="d1",
        index=0
    )
    assert turn.text() is None
    assert turn.speaker() == "Sam"
    assert turn.dialogue() == "d1"
    assert turn.index() == 0
    
def test_id_column_uniqueness():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0, None],
        ["I'm okay, you?", "Alex", "d1", 1, None],
        ["Good.", "Sam", "d1", 2, None],
        ["What's your deal?", "Alex", "d1", 3, None],
    ])
    assert len(set(turns.id)) == 4
    assert turns().id is turns.id

def test_row_indexing():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d1", 3],
    ])
    third = turns[2]
    assert third.text() == "Good."
    assert third.speaker() == "Sam"
    assert third.dialogue() == "d1"
    assert third.index() == 2

def test_row_select_by_id():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0, 'a'],
        ["I'm okay, you?", "Alex", "d1", 1, 'b'],
        ["Good.", "Sam", "d1", 2, 'c'],
        ["What's your deal?", "Alex", "d1", 3, 'd'],
    ])
    third = turns['c']
    assert third.id() == 'c'
    assert third.text() == "Good."
    middle_two = turns[['b', 'c']]
    assert list(middle_two.text) == ["I'm okay, you?", "Good."]

def test_column_selection():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d1", 3],
    ])
    speakers_and_text = turns[[turns.speaker, turns.text]]
    assert list(speakers_and_text()) == [turns.speaker, turns.text]
    assert list(speakers_and_text.speaker) == [
        "Sam", "Alex", "Sam", "Alex"
    ]
    assert list(speakers_and_text.text) == [
        "Hello my name is Sam, how are you?",
        "I'm okay, you?",
        "Good.",
        "What's your deal?",
    ]
    assert speakers_and_text.dialogue is None

def test_row_slicing():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d1", 3],
    ])
    middle_two = turns[1:3]
    assert list(middle_two.speaker) == ["Alex", "Sam"]
    assert list(middle_two.text) == ["I'm okay, you?", "Good."]
    assert list(middle_two.dialogue) == ["d1", "d1"]

def test_row_multiselect():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d1", 3],
    ])
    sam_only = turns[[0, 2]]
    assert list(sam_only.speaker) == ["Sam", "Sam"]
    assert list(sam_only.text) == [
        "Hello my name is Sam, how are you?",
        "Good."
    ]

def test_row_filtering():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d1", 3],
    ])
    sam_only = turns[[True, False, True, False]]
    assert list(sam_only.speaker) == ["Sam", "Sam"]
    assert list(sam_only.text) == [
        "Hello my name is Sam, how are you?",
        "Good."
    ]

def test_nested_select():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d1", 3],
    ])
    subturns = turns[1:]
    sub_speakertexts = subturns[[subturns.speaker, subturns.text]]
    subsub = sub_speakertexts[:-1]
    assert list(subsub.speaker) == ["Alex", "Sam"]
    assert list(subsub.text) == ["I'm okay, you?", "Good."]
    assert subsub.dialogue is None

def test_row_iteration():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1]
    ])
    rows = list(turns)
    assert len(rows) == 2
    assert rows[0].speaker() == "Sam"
    assert rows[1].speaker() == "Alex"

def test_zipping_iteration():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d1", 3],
    ])
    zipped = list(zip(*turns[turns.text, turns.speaker]()))
    for i, (text, speaker) in enumerate(zipped):
        assert text == turns.text[i]
        assert speaker == turns.speaker[i]

def test_row_mutation():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d1", 3],
    ])
    row = ["I'm terrible!", "Alex", "d1", 8]
    turns[1] = row
    assert list(turns.text) == [
        "Hello my name is Sam, how are you?",
        "I'm terrible!",
        "Good.",
        "What's your deal?",
    ]
    assert turns[1]().item() == row

def test_multirow_mutation():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d1", 3],
    ])
    mutation = [
        ("I'm terrible!", "Alex", "d1", 8),
        ("Oh no!", "Sam", "d1", 9),
    ]
    turns[1:3] = mutation
    assert list(turns.text) == [
        "Hello my name is Sam, how are you?",
        "I'm terrible!",
        "Oh no!",
        "What's your deal?",
    ]
    assert list(zip(*turns[1:3]())) == mutation

def test_detachment():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d1", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d1", 3],
    ])
    detached = ~turns[turns.text, turns.speaker][1:3]
    assert list(detached.text) == [
        "I'm okay, you?",
        "Good."
    ]
    assert list(detached.speaker) == ["Alex", "Sam"]
    assert detached.dialogue is None
    detached[0] = ["I'm terrible!", "Alex"]
    assert list(detached.text) == [
        "I'm terrible!",
        "Good."
    ]
    assert list(turns.text) == [
        "Hello my name is Sam, how are you?",
        "I'm okay, you?",
        "Good.",
        "What's your deal?",
    ]

def test_inner_join():
    a = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d0", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d3", 3],
    ])
    b = Dialogue.of([
        ["d1", "Sam", "How's the weather?"],
        ["d2", "Sam", "It's nice!"],
        ["d3", "Alex", "That's good."],
    ])
    joined = a[[a.dialogue]] & b[[b.id]]
    assert [c.name for c in joined()] == [
        'text', 'speaker', 'dialogue', 'index',
        'sys', 'text'
    ]
    assert list(joined.text) == [
        "Hello my name is Sam, how are you?",
        "Good.",
        "What's your deal?"
    ]
    assert list(joined().R.text) == [
        "How's the weather?",
        "How's the weather?",
        "That's good."
    ]
    
def test_inner_join_subrows():
    a = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d0", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d3", 3],
    ])
    b = Dialogue.of([
        ["d1", "Sam", "How's the weather?"],
        ["d2", "Sam", "It's nice!"],
        ["d3", "Alex", "That's good."],
    ])
    joined = a[[a.dialogue]][[0, 3]] & b[[b.id]]
    assert [c.name for c in joined()] == [
        'text', 'speaker', 'dialogue', 'index',
        'sys', 'text'
    ]
    assert list(joined.text) == [
        "Hello my name is Sam, how are you?",
        "What's your deal?"
    ]
    assert list(joined().R.text) == [
        "How's the weather?",
        "That's good."
    ]
    
def test_left_join():
    a = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d0", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d3", 3],
    ])
    b = Dialogue.of([
        ["d1", "Sam", "How's the weather?"],
        ["d2", "Sam", "It's nice!"],
        ["d3", "Alex", "That's good."],
    ])
    joined = a.dialogue << b.id
    assert [c.name for c in joined()] == [
        'text', 'speaker', 'dialogue', 'index',
        'sys', 'text'
    ]
    assert list(joined.text) == [
        "Hello my name is Sam, how are you?",
        "Good.",
        "I'm okay, you?",
        "What's your deal?"
    ]
    assert list(joined().R.text) == [
        "How's the weather?",
        "How's the weather?",
        None,
        "That's good."
    ]

def test_outer_join():
    a = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d0", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d3", 3],
    ])
    b = Dialogue.of([
        ["d1", "Sam", "How's the weather?"],
        ["d2", "Sam", "It's nice!"],
        ["d3", "Alex", "That's good."],
    ])
    joined = a.dialogue | b.id
    assert [c.name for c in joined()] == [
        'text', 'speaker', 'dialogue', 'index',
        'sys', 'text'
    ]
    assert list(joined.text) == [
        "Hello my name is Sam, how are you?",
        "Good.",
        None,
        "What's your deal?",
        "I'm okay, you?"
    ]
    assert list(joined().R.text) == [
        "How's the weather?",
        "How's the weather?",
        "It's nice!",
        "That's good.",
        None
    ]

def test_cartesian_join():
    a = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d0", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d3", 3],
    ])
    b = Dialogue.of([
        ["d1", "Sam", "How's the weather?"],
        ["d2", "Sam", "It's nice!"],
        ["d3", "Alex", "That's good."],
    ])
    joined = a[a.text, a.speaker] @ b[b.text]
    assert [c.name for c in joined()] == [
        'text', 'speaker', 'text'
    ]
    assert list(joined.text) == [
        "Hello my name is Sam, how are you?",
        "Hello my name is Sam, how are you?",
        "Hello my name is Sam, how are you?",
        "I'm okay, you?",
        "I'm okay, you?",
        "I'm okay, you?",
        "Good.",
        "Good.",
        "Good.",
        "What's your deal?",
        "What's your deal?",
        "What's your deal?"
    ]
    assert list(joined().R.text) == [
        "How's the weather?",
        "It's nice!",
        "That's good.",
        "How's the weather?",
        "It's nice!",
        "That's good.",
        "How's the weather?",
        "It's nice!",
        "That's good.",
        "How's the weather?",
        "It's nice!",
        "That's good."
    ]


    
def test_column_to_table():
    c = ez.Column([
        'a', 'b', 'c'
    ], name='letters')
    t = c.table()
    assert isinstance(t, ez.Table)
    assert list(t.letters) == ['a', 'b', 'c']
    assert len(t) == 3
    assert len(t()) == 1

def test_create_empty_table():
    t = Turn.of([])
    assert len(t) == 0
    assert len(t()) == 5

def test_apply_to_column():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d0", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d3", 3],
    ])
    def lowering(x:Turn):
        return x.text().lower()
    lowered = turns().apply(lowering)
    assert lowered == [
        "hello my name is sam, how are you?",
        "i'm okay, you?",
        "good.",
        "what's your deal?"
    ]
    assert isinstance(lowered, ez.Column)
    assert lowered.name == 'lowering'
    
def test_apply_to_table():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d0", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d3", 3],
    ])
    def lowering(x:Turn):
        return dict(
            text=x.text().lower(),
            person=x.speaker().lower()
        )
    lowered = turns().apply(lowering)
    assert list(lowered.text) == [
        "hello my name is sam, how are you?",
        "i'm okay, you?",
        "good.",
        "what's your deal?"
    ]
    assert list(lowered.person) == [
        "sam",
        "alex",
        "sam",
        "alex"
    ]
    assert isinstance(lowered, ez.Table)

def test_apply_with_params():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["I'm okay, you?", "Alex", "d0", 1],
        ["Good.", "Sam", "d1", 2],
        ["What's your deal?", "Alex", "d3", 3],
    ])
    def first_four(text, dialogue):
        return text[:4]
    ff = turns().apply(first_four)
    assert ff == [
        "Hell",
        "I'm ",
        "Good",
        "What"
    ]
    assert isinstance(ff, ez.Column)
    assert ff.name == 'first_four'

def test_sort():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0, 'a'],
        ["What's your deal?", "Alex", "d3", 3, 'b'],
        ["Good.", "Sam", "d1", 2, 'c'],
        ["I'm okay, you?", "Alex", "d0", 1, 'd'],
    ])
    turns().sort(turns.dialogue)
    assert list(turns.dialogue) == [
        "d0",
        "d1",
        "d1",
        "d3"
    ]
    assert list(turns.id) == [
        'd', 'a', 'c', 'b'
    ]

def test_sort_with_views():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0, 'a'],
        ["What's your deal?", "Alex", "d3", 3, 'b'],
        ["Something weather", "Alex", "d3", 5, 'c'],
        ["Good.", "Sam", "d1", 2, 'd'],
        ["I'm okay, you?", "Alex", "d0", 1, 'e'],
        ["Blah blah", "Sam", "d1", 4, 'f'],
    ])
    view = turns[1:-1]
    ordered = view().sort(view.dialogue)
    assert list(turns.dialogue) == [
        "d1",
        "d3",
        "d3",
        "d1",
        "d0",
        "d1"
    ]
    assert list(ordered.dialogue) == [
        "d0",
        "d1",
        "d3",
        "d3"
    ]
    assert list(ordered.id) == [
        'e', 'd', 'b', 'c'
    ]
    assert list(turns.id) == [
        'a', 'b', 'c', 'd', 'e', 'f'
    ]

def test_group():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["What's your deal?", "Alex", "d3", 3],
        ["Something weather", "Alex", "d3", 5],
        ["Good.", "Sam", "d1", 2],
        ["I'm okay, you?", "Alex", "d0", 1],
        ["Blah blah", "Sam", "d1", 4],
    ])
    grouped = turns().group(turns.dialogue)
    assert set(grouped) == {'d0', 'd1', 'd3'}
    assert set(grouped['d1'].text) == {
        "Hello my name is Sam, how are you?",
        "Good.",
        "Blah blah"
    }

def test_concatenate_constructor():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0],
        ["What's your deal?", "Alex", "d3", 3],
        ["Something weather", "Alex", "d3", 5],
        ["Good.", "Sam", "d1", 2],
        ["I'm okay, you?", "Alex", "d0", 1],
        ["Blah blah", "Sam", "d1", 4],
    ])
    grouped = turns().group(turns.dialogue)
    examples = {
        group: subtable[0]
        for group, subtable in grouped.items()
    }
    example_table = ez.Table.of(*examples.values())
    assert len(example_table) == 3
    assert list(example_table.dialogue) == ['d1', 'd3', 'd0']
    assert list(example_table.text) == [
        "Hello my name is Sam, how are you?",
        "What's your deal?",
        "I'm okay, you?"
    ]
        
def test_save_and_load():
    turns = Turn.of([
        ["Hello my name is Sam, how are you?", "Sam", "d1", 0, 'a'],
        ["What's your deal?", "Alex", "d3", 3, 'b'],
        ["Something weather", "Alex", "d3", 5, 'c']
    ])
    turns().save('test/foo/testfile.csv')
    loaded = Turn.of('test/foo/testfile.csv')
    assert list(loaded.text) == [
        "Hello my name is Sam, how are you?",
        "What's your deal?",
        "Something weather"
    ]
    assert isinstance(loaded.id, ez.IDColumn)

def test_create_table_from_rows_anonymous_columns():
    table = ez.Table.of([[1, 2, 3],[4, 5, 6]])
    assert list(table.A) == [1, 4]
    assert list(table.B) == [2, 5]
    assert list(table.C) == [3, 6]
