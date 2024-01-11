import ezpyzy as ez
import dataclasses as dc


@dc.dataclass
class Foo(ez.Table):
    id: ez.ColID = None
    name: ez.ColStr = None
    age: ez.ColInt = None

table = Foo.of([
    ['1', 'Alice', 20],
    ['2', 'Bob', 21],
    ['3', 'Charlie', 22],
])

print(table)