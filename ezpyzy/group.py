
import typing as T



A = T.TypeVar('A')
B = T.TypeVar('B')

@T.overload
def group(items: T.Iterable[A]) -> T.Dict[A, T.List[A]]:
    pass
@T.overload
def group(items: T.Iterable[A], by: T.Iterable[B]|T.Callable[[A], B]) -> T.Dict[B, T.List[A]]:
    pass
def group(items, by=None):
    groups = {}
    if callable(by):
        by = map(by, items)
    elif by is None:
        by = items
    for item, key in zip(items, by):
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups



if __name__ == '__main__':
    print_groups = lambda groups: print(
        '\n'.join(f'{k}: {", ".join(str(x) for x in v)}' for k, v in groups.items()), '\n')

    items = 'abcdefabcageff'
    char_groups = group(items)
    print_groups(char_groups)

    items = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    odd_even_groups = group(items, lambda x: frozenset((x % 2,)))
    print_groups(odd_even_groups)

    items = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    groups = ['a', 'b', 'c', 'a', 'e', 'b', 'g', 'a', 'a']
    int_groups = group(items, groups)
    print_groups(int_groups)
