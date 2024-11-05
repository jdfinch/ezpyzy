

import typing as T


A = T.TypeVar('A')
B = T.TypeVar('B')

def sort(items: T.Iterable[A], by: T.Iterable[B]|T.Callable[[A], B]|None=None, reverse: bool=False) -> T.List[A]:
    if by is None:
        return sorted(items, reverse=reverse)
    elif callable(by):
        return sorted(items, key=by, reverse=reverse)
    else:
        return [x for _, x in sorted(zip(by, items), key=lambda item: item[0], reverse=reverse)]



if __name__ == '__main__':

    items = [4, 2, 3, 1, 5]
    sorted_items = sort(items)
    print(sorted_items)

    scores = [0.1, 0.5, 0.2, 0.3, 0.4]
    sorted_items = sort(items, scores, reverse=True)
    print(sorted_items)
