

instances = {}

class SingletonMeta(type):
    def __call__(cls, *args, **kwargs):
        if cls not in instances:
            instances[cls] = super().__call__(*args, **kwargs)
        instance = instances[cls]
        return instance

class Singleton(metaclass=SingletonMeta):
    pass


if __name__ == '__main__':
    class Foo(Singleton):
        def __init__(self, x):
            self.x = x
            print(f"Foo.__init__ {self.x}")

    class Bar(Singleton):
        def __init__(self, y):
            self.y = y


    foo1 = Foo(1)
    foo2 = Foo(2)
    print(type(foo1), id(foo1), vars(foo1))
    print(type(foo2), id(foo2), vars(foo2))

    bar1 = Bar(1)
    bar2 = Bar(2)
    print(type(bar1), id(bar1), vars(bar1))
    print(type(bar2), id(bar2), vars(bar2))
    print(type(foo1), id(foo1), vars(foo1))
    print(type(foo2), id(foo2), vars(foo2))