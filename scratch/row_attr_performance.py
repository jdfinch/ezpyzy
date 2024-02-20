
from ezpyzy import Timer

class RowTuple:
    __slots__ = 'a', 'b', 'c', 'd'
    def __init__(self, a, b, c, d=None):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

class RowFallthrough:
    __slots__ = 'a', 'b', 'd'
    def __init__(self, a, b, d):
        self.a = a
        self.b = b
        self.d = d
    def __getattr__(self, item):
        return getattr(self.d, item)

control = [[i, i, i, i] for i in range(10**7)]
table = [RowTuple(i, i, i) for i in range(10**7)]
double = [RowTuple(i, i, i, table[i]) for i in range(10**7)]
falls = [RowFallthrough(i, i, table[i]) for i in range(10**7)]

with Timer('Iter control'):
    for row in control:
        x = row[0]

with Timer('Iter rows get attr'):
    for row in table:
        x = row.a

with Timer('Iter rows get attr two hop'):
    for row in double:
        x = row.d.a

with Timer('Iter rows get attr fallthrough'):
    for row in falls:
        x = row.c


class RowTuple:
    # __slots__ = 'a', 'b', 'c', 'd'
    def __init__(self, a, b, c, d=None):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

class RowFallthrough:
    # __slots__ = 'a', 'b', 'd'
    def __init__(self, a, b, d):
        self.a = a
        self.b = b
        self.d = d
    def __getattr__(self, item):
        return getattr(self.d, item)

control = [[i, i, i, i] for i in range(10**7)]
table = [RowTuple(i, i, i) for i in range(10**7)]
double = [RowTuple(i, i, i, table[i]) for i in range(10**7)]
falls = [RowFallthrough(i, i, table[i]) for i in range(10**7)]

with Timer('Iter control no slots'):
    for row in control:
        x = row[0]

with Timer('Iter rows get attr no slots'):
    for row in table:
        x = row.a

with Timer('Iter rows get attr two hop no slots'):
    for row in double:
        x = row.d.a

with Timer('Iter rows get attr fallthrough no slots'):
    for row in falls:
        x = row.c


class PropertyRow:
    __slots__ = '_a', '_b', '_c', '_d'
    def __init__(self, a, b, c, d=None):
        self._a = a
        self._b = b
        self._c = c
        self._d = d

    @property
    def a(self):
        return self._a
    @a.setter
    def a(self, value):
        self._a = value
    @property
    def b(self):
        return self._b
    @b.setter
    def b(self, value):
        self._b = value
    @property
    def c(self):
        return self._c
    @c.setter
    def c(self, value):
        self._c = value
    @property
    def d(self):
        return self._d
    @d.setter
    def d(self, value):
        self._d = value


table = [PropertyRow(i, i, i) for i in range(10 ** 7)]
double = [PropertyRow(i, i, i, table[i]) for i in range(10 ** 7)]

with Timer('Iter rows with property'):
    for row in table:
        x = row.a

with Timer('Iter rows with property two hop'):
    for row in double:
        x = row.d.a

with Timer('Iter rows setter'):
    for row in table:
        row.a = 0


# class MyDescriptor:
#     def __init__(self, name):
#         self.name = '__'+name
#     def __get__(self, instance, owner):
#         return getattr(instance, self.name)
#     def __set__(self, instance, value):
#         setattr(instance, self.name, value)


def MyDescriptor(name):
    name = '__'+name
    def get(self):
        return getattr(self, name)
    def set(self, value):
        setattr(self, name, value)
    def delete(self):
        delattr(self, name)
    return property(get, set, delete)

class DescriptorRow:
    a = MyDescriptor('a')
    b = MyDescriptor('b')
    c = MyDescriptor('c')
    d = MyDescriptor('d')
    def __init__(self, a, b, c, d=None):
        self.a = a
        self.b = b
        self.c = c
        self.d = d

table = [DescriptorRow(i, i, i) for i in range(10 ** 7)]
double = [DescriptorRow(i, i, i, table[i]) for i in range(10 ** 7)]

with Timer('Iter rows with descriptor'):
    for row in table:
        x = row.a

with Timer('Iter rows with descriptor two hop'):
    for row in double:
        x = row.d.a

with Timer('Iter rows with descriptor setter'):
    for row in table:
        row.a = 0



class MyNoneGet:
    def __init__(self, name):
        self.a = name
    def __getattr__(self, item):
        return None

class NoneGetWithClassAttr:
    def __init__(self, name):
        self.a = name
    def __getattr__(self, item):
        setattr(type(self), item, None)
        return None

table = [MyNoneGet(i) for i in range(10 ** 7)]

with Timer('Iter rows with none get'):
    for row in table:
        x = row.b

table = [NoneGetWithClassAttr(i) for i in range(10 ** 7)]

with Timer('Iter rows with none get with class attr'):
    for row in table:
        x = row.b