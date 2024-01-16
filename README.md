# ezpyzy

Utility functions solving common but annoying problems.

## Installation

```bash
pip install ezpyzy
```

## Usage

```python
import ezpyzy as ez
```

### Easily save and load .txt, .json, .csv, and .pkl

```python
text_file = ez.File('foo.txt')
json_file = ez.File('bar.json')
csv_file = ez.File('baz.csv')
pkl_file = ez.File('qux.pkl')

text_file.save('Hello, world!')
json_file.save({'a': 1, 'b': 2})
csv_file.save([[1, 2], [3, 4]])
pkl_file.save({1, 2, 3, 4})

assert text_file.load() == 'Hello, world!'
assert json_file.load() == {'a': 1, 'b': 2}
assert csv_file.load() == [[1, 2], [3, 4]]
assert pkl_file.load() == {1, 2, 3, 4}
```

### Easily cache function results in a file

```python
@ez.autocache
def heavy_workload():
    ...
    return {'a': 1, 'b': 2} 

x = heavy_workload(save='foo.json')  # Save result after calculating
x = heavy_workload(load='foo.json')  # Load result without calculating
```

### Capture all args passed to a function in a dict

```python
@ez.allargs
def foo(a, b, c, allargs=None):
    print(allargs)
    return a + b + c

foo(1, 2, 3)  # Prints {'a': 1, 'b': 2, 'c': 3}
```


### Automatically fill parameters by default with object attributes

```python
@dc.dataclass
class Foo:
    a: int
    b: int
    c: int

    @ez.update_settings
    def bar(self, a=None, b=None, c=None):
        return a + b + c


foo = Foo(0, 1, 2)
print(foo.bar(5))  # Prints 8
```

### Replace dataclass attributes by mutation with type hinting

```python
@dc.dataclass
class Foo:
    a: int
    b: int
    c: int

foo = Foo(0, 1, 2)
ez.replace(foo, b=3, c=5)
print(foo)  # Prints Foo(a=0, b=3, c=5)

with ez.replace(foo, a=2):
    print(foo)  # Prints Foo(a=2, b=3, c=5)
print(foo)  # Prints Foo(a=0, b=3, c=5)
```

### Bind arguments (functools.partial) with type hinting

```python
def foo(a: int, b: int, c: int):
    return a + b + c

bar = ez.bind(foo)(a=1, b=2)

print(bar(c=3))  # Prints 6
```

### Easy notification emails

```python
ez.email(
    'recipient@gmail.com',
    'Subject Line',
    """Body of email.""",
)
```

To use, create a file ~/.pw/gmail.json (easiest to use an app password using gmail).

```text
{
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "address@gmail.com",
    "sender_password": "app_password"
}
```

### Automatically generate human-readable names for objects

```python
print(ez.denominate())  # Prints a cool name like "DaringBespin" 
```

### Automatically generate a short-ish UUID (12 chars)

```python
print(ez.uuid())  # Prints something like "A5_H2ka4f33S"
```

### Shushes stdout and stderr

```python
with ez.shush():
    print('This will not print.')
```

### Quick hacky way to run sequential tests

```python
with check("My first test"):
    x = [1, 2, 3]
    assert x[0] == 1
    
with check("My second test"):
    x[1] = 4
    assert sum(x) == 8
```

### Print-style debugging that keeps variables from the previous run

Kind of like if jupyter notebook had a baby with using a bunch of print statements to debug code.

```python
data = load_data_for_a_long_time()
ez.explore() # Prints nearby variables and pauses execution

process_data() # will not run yet
```

After moving the `explore()` call and hitting enter...

```python
data = load_data_for_a_long_time() # will not run again

process_data() # will run now
ez.explore() # Prints nearby variables and pauses execution
```

### Dataframes but with type hinting

```python
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

for row in table:
    print(row().name) # Type hinted. Prints Alice, Bob, Charlie

print(table)
```

```text
Foo Table: 3 cols x 3 rows
id|name   |age
--|-------|---
1 |Alice  |20 
2 |Bob    |21 
3 |Charlie|22 
```








