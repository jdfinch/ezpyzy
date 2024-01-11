
import atexit
import ezpyzy as ez
import pathlib as pl
import typing as T


stores = {}


class StoreMeta(type):

    def __call__(cls, path:ez.filelike, *args, save_on_exit=True, **kwargs):
        path = ez.File(path).path
        if path not in stores:
            instance = super().__call__(path, *args, **kwargs)
            stores[path] = (instance, save_on_exit)
        instance = stores[path][0]
        assert isinstance(instance, cls), f"Store exists at {path} but is not an instance of {cls}"
        return instance


D = T.TypeVar('D')

class Store(T.Generic[D], metaclass=StoreMeta):

    def __init__(
        self,
        path: ez.filelike,
        data:D|None=None,
        format:ez.formatlike=None,
        save_on_exit:bool=True,
    ):
        self._file = ez.File(path, format=format)
        if data is None and self._file.path.exists():
            self.load()
        else:
            self.data = data

    def save(self, *args, **kwargs):
        self._file.save(self.data, *args, **kwargs)

    def load(self, *args, **kwargs):
        self.data = self._file.load(*args, **kwargs)

    @property
    def path(self):
        return self._file.path

    @property
    def format(self):
        return self._file.format

    @property
    def save_on_exit(self):
        return stores[self.path][1]

    @save_on_exit.setter
    def save_on_exit(self, value):
        stores[self.path] = (stores[self.path][0], value)

    def exists(self):
        return self.path.exists()


def save_on_exit():
    for path, (store, save_on_exit) in stores.items():
        if save_on_exit:
            store.save()

atexit.register(save_on_exit)



if __name__ == '__main__':

    foo = Store(path='foo.json')
    print(foo.data)
    foo.data = {'x': 1, 'y': 2, 'z': 3}

    bar = Store(path='bar.json')
