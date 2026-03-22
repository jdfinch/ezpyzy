from dataclasses import dataclass

from ezpyzy.table import Table


@dataclass(frozen=True)
class Nested:
    value: int


@dataclass(frozen=True)
class Row:
    id: int
    value: int


@dataclass(frozen=True)
class LeftRow:
    id: int
    fk: int
    value: str


@dataclass(frozen=True)
class RightRow:
    id: int
    group: str


@dataclass
class AttrRow:
    id: int
    name: str
    nested: Nested | None = None


class SlotRow:
    __slots__ = ("id", "label")

    def __init__(self, id, label):
        self.id = id
        self.label = label


def test_init_accepts_multiple_iterables_and_key():
    rows = [Row(1, 10), Row(2, 20), Row(3, 30)]

    table = Table(rows[:2], rows[2:], key=lambda row: row.id)

    assert list(table) == rows
    assert len(table) == 3
    assert table.key is not None
    assert table.ids == {1: 0, 2: 1, 3: 2}


def test_key_setter_builds_and_clears_ids():
    table = Table([Row(1, 10), Row(2, 20)])

    table.key = lambda row: row.id

    assert table.key is not None
    assert table.ids == {1: 0, 2: 1}

    table.key = None

    assert table.key is None
    assert table.ids is None


def test_key_setter_errors_on_collisions():
    table = Table([Row(1, 10), Row(2, 20)])

    try:
        table.key = lambda row: 1
    except AssertionError as error:
        assert "collision" in str(error).lower()
    else:
        assert False, "Expected an AssertionError for an id collision"


def test_add_unkeyed_appends_and_keyed_ignores_existing_id():
    table = Table([1, 2])
    table.add(3)
    assert list(table) == [1, 2, 3]

    rows = [Row(1, 10), Row(2, 20)]
    keyed = Table(rows, key=lambda row: row.id)
    keyed.add(Row(3, 30))
    keyed.add(Row(3, 99))

    assert list(keyed) == [rows[0], rows[1], Row(3, 30)]
    assert keyed.ids == {1: 0, 2: 1, 3: 2}


def test_insert_unkeyed_and_keyed_insert_at_index():
    table = Table([1, 3])
    table.insert(2, 1)
    assert list(table) == [1, 2, 3]

    rows = [Row(1, 10), Row(3, 30)]
    keyed = Table(rows, key=lambda row: row.id)
    inserted = Row(2, 20)
    keyed.insert(inserted, 1)

    assert list(keyed) == [rows[0], inserted, rows[1]]
    assert keyed.ids == {1: 0, 2: 1, 3: 2}


def test_insert_keyed_errors_on_duplicate_id():
    rows = [Row(1, 10), Row(2, 20)]
    table = Table(rows, key=lambda row: row.id)

    try:
        table.insert(Row(2, 99), 1)
    except AssertionError as error:
        assert "already exists" in str(error)
    else:
        assert False, "Expected an AssertionError for a duplicate inserted id"


def test_append_returns_self_and_errors_on_duplicate_key():
    rows = [Row(1, 10)]
    table = Table(rows, key=lambda row: row.id)

    appended = table.append(Row(2, 20))

    assert appended is table
    assert table.ids == {1: 0, 2: 1}

    try:
        table.append(Row(2, 99))
    except AssertionError as error:
        assert "already exists" in str(error)
    else:
        assert False, "Expected an AssertionError for a duplicate append id"


def test_extend_returns_self_and_supports_generators_for_keyed_tables():
    rows = [Row(1, 10), Row(2, 20)]
    table = Table(rows, key=lambda row: row.id)

    extended = table.extend(Row(i, i * 10) for i in [3, 4])

    assert extended is table
    assert list(table) == rows + [Row(3, 30), Row(4, 40)]
    assert table.ids == {1: 0, 2: 1, 3: 2, 4: 3}


def test_extend_keyed_errors_on_duplicate_id():
    table = Table([Row(1, 10)], key=lambda row: row.id)

    try:
        table.extend([Row(1, 99)])
    except AssertionError as error:
        assert "already exists" in str(error)
    else:
        assert False, "Expected an AssertionError for duplicate ids in extend"


def test_update_returns_self_ignores_existing_ids_and_updates_ids_mapping():
    rows = [Row(1, 10), Row(2, 20)]
    table = Table(rows, key=lambda row: row.id)

    updated = table.update([Row(2, 99), Row(3, 30)])

    assert updated is table
    assert list(table) == rows + [Row(3, 30)]
    assert table.ids == {1: 0, 2: 1, 3: 2}


def test_iter_and_len_reflect_rows():
    table = Table(["a", "b", "c"])

    assert list(iter(table)) == ["a", "b", "c"]
    assert len(table) == 3


def test_copy_returns_shallow_copy_with_same_key():
    rows = [AttrRow(1, "a", Nested(10)), AttrRow(2, "b", Nested(20))]
    table = Table(rows, key=lambda row: row.id)

    copied = table.copy()

    assert copied is not table
    assert copied.rows is not table.rows
    assert copied.ids is not table.ids
    assert copied.key is table.key
    assert list(copied) == rows
    assert copied.rows[0] is table.rows[0]
    assert copied.ids == {1: 0, 2: 1}


def test_clear_empties_in_place_and_preserves_containers():
    rows = [Row(1, 10), Row(2, 20)]
    table = Table(rows, key=lambda row: row.id)
    rows_ref = table.rows
    ids_ref = table.ids

    cleared = table.clear()

    assert cleared is table
    assert list(table) == []
    assert table.rows is rows_ref
    assert table.ids is ids_ref
    assert table.ids == {}


def test_try_map_returns_none_for_missing_values_and_raises_for_real_attribute_errors():
    rows = [AttrRow(1, "a", Nested(10)), AttrRow(2, "b", None)]
    table = Table(rows, key=lambda row: row.id)

    gotten = table.try_map(lambda row: row.nested.value)

    assert list(gotten) == [10, None]

    try:
        table.try_map(lambda row: row.missing)
    except AttributeError:
        pass
    else:
        assert False, "Expected an AttributeError for a genuinely missing attribute"


def test_map_returns_new_table_of_transformed_values():
    table = Table([1, 2, 3])

    gotten = table.map(lambda item: item * 10)

    assert list(gotten) == [10, 20, 30]
    assert gotten is not table


def test_get_fetches_single_row_by_id():
    rows = [Row(1, 10), Row(2, 20)]
    table = Table(rows, key=lambda row: row.id)

    gotten = table.get(2)

    assert gotten == rows[1]


def test_get_by_id_requires_keyed_table_and_missing_key_errors():
    table = Table([1, 2, 3])

    try:
        table.get(1)
    except AssertionError as error:
        assert "no key" in str(error)
    else:
        assert False, "Expected an AssertionError when getting by id from an unkeyed table"

    rows = [Row(1, 10)]
    keyed = Table(rows, key=lambda row: row.id)
    try:
        keyed.get(2)
    except KeyError:
        pass
    else:
        assert False, "Expected a KeyError when getting a missing id"


def test_try_get_fetches_single_row_or_none_by_id():
    rows = [Row(1, 10), Row(2, 20)]
    table = Table(rows, key=lambda row: row.id)

    assert table.try_get(2) == rows[1]
    assert table.try_get(3) is None

    unkeyed = Table([1, 2, 3])
    try:
        unkeyed.try_get(1)
    except AssertionError as error:
        assert "no key" in str(error)
    else:
        assert False, "Expected an AssertionError when trying to get by id from an unkeyed table"


def test_keys_items_and_has_use_key_order():
    rows = [Row(1, 10), Row(2, 20), Row(3, 30)]
    table = Table(rows, key=lambda row: row.id)

    assert list(table.keys()) == [1, 2, 3]
    assert list(table.items()) == [(1, rows[0]), (2, rows[1]), (3, rows[2])]
    assert table.has(2) is True
    assert table.has(4) is False


def test_keys_items_and_has_require_keyed_table():
    table = Table([1, 2, 3])

    for method in (table.keys, table.items, lambda: table.has(1)):
        try:
            method()
        except AssertionError as error:
            assert "no key" in str(error)
        else:
            assert False, "Expected an AssertionError on an unkeyed table"


def test_filter_by_predicate():
    table = Table([1, 2, 3, 4])

    filtered = table.filter(lambda item: item % 2 == 0)

    assert filtered is table
    assert list(filtered) == [2, 4]
    assert list(table) == [2, 4]


def test_filter_by_boolean_mask():
    table = Table(["a", "b", "c"])

    filtered = table.filter([True, False, True])

    assert filtered is table
    assert list(filtered) == ["a", "c"]


def test_filter_by_ids():
    rows = [Row(1, 10), Row(2, 20), Row(3, 30)]
    table = Table(rows, key=lambda row: row.id)

    filtered = table.filter({1, 3})

    assert filtered is table
    assert list(filtered) == [rows[0], rows[2]]
    assert filtered.key is not None
    assert filtered.ids == {1: 0, 3: 1}


def test_filter_by_mask_requires_same_length():
    table = Table([1, 2, 3])

    try:
        table.filter([True, False])
    except AssertionError as error:
        assert "same length" in str(error)
    else:
        assert False, "Expected an AssertionError for a mismatched filter mask"


def test_select_preserves_requested_id_order():
    rows = [Row(1, 10), Row(2, 20), Row(3, 30)]
    table = Table(rows, key=lambda row: row.id)

    selected = table.select([3, 1])

    assert selected is not table
    assert list(selected) == [rows[2], rows[0]]
    assert list(table) == rows
    assert selected.ids == {3: 0, 1: 1}


def test_select_requires_keyed_table():
    table = Table([1, 2, 3])

    try:
        table.select([1, 2])
    except AssertionError as error:
        assert "no key" in str(error)
    else:
        assert False, "Expected an AssertionError when selecting from an unkeyed table"


def test_getitem_by_slice_returns_new_table():
    table = Table([1, 2, 3, 4])

    selected = table[1:3]

    assert selected is not table
    assert list(selected) == [2, 3]
    assert list(table) == [1, 2, 3, 4]


def test_getitem_by_indices_preserves_requested_order():
    rows = [Row(1, 10), Row(2, 20), Row(3, 30)]
    table = Table(rows, key=lambda row: row.id)

    selected = table[[2, 0]]

    assert list(selected) == [rows[2], rows[0]]
    assert selected.ids == {3: 0, 1: 1}

def test_slice_mutates_in_place():
    table = Table([1, 2, 3, 4])
    rows = table.rows

    sliced = table.slice([3, 1])

    assert sliced is table
    assert list(table) == [4, 2]
    assert table.rows is rows


def test_group_returns_keyed_subtables_and_preserves_row_order():
    rows = [Row(1, 10), Row(2, 11), Row(3, 12)]
    table = Table(rows, key=lambda row: row.id)

    groups = table.group(lambda row: row.value % 2)

    assert list(groups[0]) == [rows[0], rows[2]]
    assert list(groups[1]) == [rows[1]]
    assert groups[0].ids == {1: 0, 3: 1}
    assert groups[1].ids == {2: 0}


def test_sort_by_callable_and_sequence_return_self():
    rows = [Row(1, 30), Row(2, 10), Row(3, 20)]
    table = Table(rows, key=lambda row: row.id)
    rows_ref = table.rows

    sorted_table = table.sort(lambda row: row.value)

    assert sorted_table is table
    assert list(table) == [rows[1], rows[2], rows[0]]
    assert table.rows is rows_ref

    sorted_table = table.sort([3, 1, 2], reverse=True)

    assert sorted_table is table
    assert list(table) == [rows[1], rows[0], rows[2]]
    assert table.rows is rows_ref


def test_sort_by_sequence_requires_same_length():
    table = Table([1, 2, 3])

    try:
        table.sort([1, 2])
    except AssertionError as error:
        assert "same length" in str(error)
    else:
        assert False, "Expected an AssertionError for mismatched sort keys"


def test_discard_by_ids_ignores_missing():
    rows = [Row(1, 10), Row(2, 20), Row(3, 30)]
    table = Table(rows, key=lambda row: row.id)
    rows_ref = table.rows
    ids_ref = table.ids

    discarded = table.discard([2, 4, 2])

    assert discarded is table
    assert list(table) == [rows[0], rows[2]]
    assert table.rows is rows_ref
    assert table.ids is ids_ref
    assert table.ids == {1: 0, 3: 1}


def test_remove_by_ids_errors_on_missing():
    rows = [Row(1, 10), Row(2, 20), Row(3, 30)]
    table = Table(rows, key=lambda row: row.id)

    try:
        table.remove([2, 4, 2])
    except AssertionError as error:
        assert "do not exist" in str(error)
    else:
        assert False, "Expected an AssertionError for missing ids"


def test_delete_by_index_sequence_deduplicates_and_mutates_in_place():
    table = Table([10, 20, 30, 40, 50])
    rows_ref = table.rows

    deleted = table.delete([3, 1, 3])

    assert deleted is table
    assert list(table) == [10, 30, 50]
    assert table.rows is rows_ref


def test_delete_by_negative_indices():
    table = Table(["a", "b", "c", "d"])

    table.delete([-1, -3])

    assert list(table) == ["a", "c"]


def test_delete_by_slice_on_keyed_table_updates_ids():
    rows = [Row(1, 10), Row(2, 20), Row(3, 30), Row(4, 40)]
    table = Table(rows, key=lambda row: row.id)
    ids_ref = table.ids

    table.delete(slice(1, 3))

    assert list(table) == [rows[0], rows[3]]
    assert table.ids is ids_ref
    assert table.ids == {1: 0, 4: 1}


def test_delete_by_index_errors_if_out_of_range():
    table = Table([1, 2, 3])

    try:
        table.delete([1, 5])
    except IndexError:
        pass
    else:
        assert False, "Expected an IndexError for an out-of-range deletion index"


def test_delitem_uses_delete_behavior():
    table = Table([1, 2, 3, 4])

    del table[[2, 0]]

    assert list(table) == [2, 4]


def test_join_defaults_to_left_join_against_right_ids():
    left = [
        LeftRow(1, 20, "a"),
        LeftRow(2, 10, "b"),
        LeftRow(3, 99, "c"),
    ]
    right = [
        RightRow(10, "x"),
        RightRow(20, "y"),
    ]
    a = Table(left, key=lambda row: row.id)
    b = Table(right, key=lambda row: row.id)

    joined = a.join(b, lambda row: row.fk)

    assert list(joined) == [
        (left[0], right[1]),
        (left[1], right[0]),
        (left[2], None),
    ]
    assert joined.key is None


def test_join_requires_right_key_or_explicit_against():
    left = [LeftRow(1, 1, "a")]
    right = [RightRow(1, "x")]
    a = Table(left, key=lambda row: row.id)
    b = Table(right)

    try:
        a.join(b, lambda row: row.fk)
    except AssertionError as error:
        assert "against" in str(error)
    else:
        assert False, "Expected an AssertionError when joining without ids or against"


def test_join_inner_uses_explicit_against_selector_and_duplicates_matches():
    left = [
        LeftRow(1, 1, "a"),
        LeftRow(2, 2, "b"),
    ]
    right = [
        RightRow(10, "x"),
        RightRow(11, "x"),
        RightRow(12, "y"),
    ]
    a = Table(left, key=lambda row: row.id)
    b = Table(right, key=lambda row: row.id)

    joined = a.join_inner(b, lambda row: row.fk, lambda row: 1 if row.group == "x" else 2)

    assert list(joined) == [
        (left[0], right[0]),
        (left[0], right[1]),
        (left[1], right[2]),
    ]


def test_join_right_preserves_right_order_and_unmatched_rows():
    left = [
        LeftRow(1, 2, "a"),
        LeftRow(2, 2, "b"),
    ]
    right = [
        RightRow(1, "x"),
        RightRow(2, "y"),
        RightRow(3, "z"),
    ]
    a = Table(left, key=lambda row: row.id)
    b = Table(right, key=lambda row: row.id)

    joined = a.join_right(b, lambda row: row.fk)

    assert list(joined) == [
        (None, right[0]),
        (left[0], right[1]),
        (left[1], right[1]),
        (None, right[2]),
    ]


def test_join_outer_includes_left_and_right_unmatched_rows():
    left = [
        LeftRow(1, 2, "a"),
        LeftRow(2, 4, "b"),
    ]
    right = [
        RightRow(2, "x"),
        RightRow(3, "y"),
    ]
    a = Table(left, key=lambda row: row.id)
    b = Table(right, key=lambda row: row.id)

    joined = a.join_outer(b, lambda row: row.fk)

    assert list(joined) == [
        (left[0], right[0]),
        (left[1], None),
        (None, right[1]),
    ]


def test_join_cartesian_returns_all_pairs():
    left = [LeftRow(1, 1, "a"), LeftRow(2, 2, "b")]
    right = [RightRow(10, "x"), RightRow(20, "y")]
    a = Table(left, key=lambda row: row.id)
    b = Table(right, key=lambda row: row.id)

    joined = a.join_cartesian(b)

    assert list(joined) == [
        (left[0], right[0]),
        (left[0], right[1]),
        (left[1], right[0]),
        (left[1], right[1]),
    ]


def test_join_index_groups_right_rows_by_selector():
    right = [RightRow(10, "x"), RightRow(11, "x"), RightRow(12, "y")]
    table = Table([LeftRow(1, 1, "a")], key=lambda row: row.id)
    other = Table(right, key=lambda row: row.id)

    index = table._join_index(other, lambda row: row.group)

    assert index == {
        "x": [(0, right[0]), (1, right[1])],
        "y": [(2, right[2])],
    }


def test_render_infers_object_attributes():
    rows = [LeftRow(1, 20, "alpha"), LeftRow(2, 30, "beta")]
    table = Table(rows, key=lambda row: row.id)

    rendered = table.render()

    assert "Table of LeftRow with 2 rows" in rendered
    assert "id" in rendered
    assert "fk" in rendered
    assert "value" in rendered
    assert "alpha" in rendered
    assert "beta" in rendered


def test_render_empty_table_returns_title_only():
    table = Table()

    assert table.render() == "Table with 0 rows"


def test_render_supports_renaming_excluding_and_computed_columns():
    rows = [LeftRow(1, 20, "alpha")]
    table = Table(rows, key=lambda row: row.id)

    rendered = table.render(cols={
        "identifier": "id",
        "fk": False,
        "summary": lambda row: f"{row.id}:{row.value}",
    })

    assert "identifier" in rendered
    assert "summary" in rendered
    assert "fk" not in rendered
    assert "1:alpha" in rendered


def test_render_infers_tuple_columns_by_position():
    table = Table([(1, "alpha"), (2, "beta", "extra")])

    rendered = table.render()

    assert "Table of tuple with 2 rows" in rendered
    assert "0" in rendered
    assert "1" in rendered
    assert "2" in rendered
    assert "extra" in rendered


def test_render_supports_true_include_and_slot_rows():
    rows = [SlotRow(1, "alpha")]
    table = Table(rows)

    rendered = table.render(cols={"id": True, "label": True})

    assert "Table of SlotRow with 1 rows" in rendered
    assert "id" in rendered
    assert "label" in rendered
    assert "alpha" in rendered


def test_render_truncates_when_width_is_small():
    rows = [LeftRow(1, 20, "abcdefghijklmnopqrstuvwxyz")]
    table = Table(rows, key=lambda row: row.id)

    rendered = table.render(width=20, cell_width=10)

    assert "abcdefgh.." in rendered
    assert all(len(line) <= 20 for line in rendered.splitlines())


def test_render_honors_max_rows():
    rows = [LeftRow(1, 20, "alpha"), LeftRow(2, 30, "beta")]
    table = Table(rows, key=lambda row: row.id)

    rendered = table.render(rows=1)

    assert "alpha" in rendered
    assert "beta" not in rendered


def test_render_does_not_shrink_columns_when_all_fit():
    rows = [LeftRow(1, 20, "abcdefghijklmnopqrstuvwxyz")]
    table = Table(rows, key=lambda row: row.id)

    rendered = table.render(width=80, cell_width=10)

    assert "abcdefghijklmnopqrstuvwxyz" in rendered
    assert "abcdefghijklmnopqr.." not in rendered


def test_render_omits_columns_to_fit_width():
    rows = [LeftRow(1, 20, "alpha")]
    table = Table(rows, key=lambda row: row.id)

    rendered = table.render(width=12, cell_width=10)

    assert ".." in rendered.splitlines()[1]
    assert all(len(line) <= 12 for line in rendered.splitlines())


def test_display_returns_rendered_string(capsys):
    rows = [LeftRow(1, 20, "alpha")]
    table = Table(rows, key=lambda row: row.id)

    rendered = table.display()
    captured = capsys.readouterr()

    assert rendered in captured.out
