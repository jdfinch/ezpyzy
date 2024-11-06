
import typing as T
from ezpyzy.peek import peek


A = T.TypeVar('A')

def select(items: T.Iterable[A], indices: T.Iterable|T.Callable[[A], T.Any]=None) -> T.List[A]:
    if callable(indices):
        indices = map(indices, items)
    if not isinstance(items, T.Sequence):
        items = list(items)
    if not isinstance(indices, T.Sequence):
        indices = list(indices)
    if isinstance(indices[0], bool):
        assert len(items) == len(indices), \
            f'Boolean slection requires items and indices to have the same length, got {len(items) = } and {len(indices) = }'
        return [item for item, index in zip(items, indices) if index]
    else:
        return [items[index] for index in indices]