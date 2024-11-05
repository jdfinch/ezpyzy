
import typing as T


def foo(x: str, y:list):
    return x + repr(y)


P = T.ParamSpec('TR')
F = T.TypeVar('F')

def decorator(f: F) -> F|T.Callable[..., list[str]]:
    def wrapper(*args, **kwargs):
        return [f(*args, **kwargs)]
    return wrapper

bar = decorator(foo)

tester = bar('hello', 'world')

tester.append(4)

print(tester)


