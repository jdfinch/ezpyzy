
from pathlib import Path
import csv, json, pickle
import cattrs.preconf.json as cjson
import typing
import io
from attrs import define, field
import atexit


default = object()


FT = typing.TypeVar('FT')


@define
class File(typing.Generic[FT]):
    path: Path = field(converter=Path)
    type: typing.Optional[typing.Type[FT]] = None
    format: 'SerializationFormat[FT]' = None
    value: typing.Optional[FT] = None
    autosave: bool = False

    def __attrs_post_init__(self):
        if self.format is None:
            self.format = formats.get(self.path.suffix)
        if self.autosave:
            atexit.register(self.save)

    def read_text(self, encoding: str|None=None, errors: str|None=None):
        return self.path.read_text(encoding=encoding, errors=errors)
    
    def read_bytes(self):
        return self.path.read_bytes()
    
    def load(self) -> FT:
        if self.format.binary:
            content = self.read_bytes()
        else:
            content = self.read_text()
        self.value = self.format.deserialize(content, self.type)
        return self.value
    
    def write_text(self, text:str, encoding:str|None=None, errors:str|None=None, newline:str|None=None):
        return self.path.write_text(text, encoding=encoding, errors=errors, newline=newline)
    
    def write_bytes(self, data):
        return self.path.write_bytes(data)
        
    def save(self, value: typing.Optional[FT] = default) -> str:
        if value is not default:
            self.value = value
        content = self.format.serialize(self.value)
        if self.format.binary:
            self.write_bytes(content)
        else:
            self.write_text(content)

    

    @property
    def extension(self):
        return self.path.suffix
    
    @property
    def name(self):
        return self.path.name
    
    @property
    def folder(self):
        return self.path.parent
    
    def __bool__(self):
        return self.path.is_file()


formats = {}


T = typing.TypeVar('T')

@define
class SerializationFormat(typing.Generic[T]):
    serialize: typing.Callable[[typing.Type[T]], str|bytes] = None
    deserialize: typing.Callable[[str|bytes], T] = None
    binary: bool = False
    extensions: tuple[str, ...] = None

    def __attrs_post_init__(self):
        for extension in self.extensions:
            formats[extension] = self

    @property
    def extension(self):
        return self.extensions[0]
    

def to_text(text: str):
    return text

def from_text(text: str, _=None):
    return text 

format_text = SerializationFormat(
    serialize=to_text,
    deserialize=from_text,
    extensions=('.txt', '.text', '.md')
)

def to_bytes(data: bytes):
    return data

def from_bytes(data: bytes, _=None):
    return data

format_bytes = SerializationFormat(
    serialize=to_bytes,
    deserialize=from_bytes,
    extensions=('.bin',)
)


def to_json(o):
    unstructured = json_converter.unstructure(o)
    serial = json.dumps(unstructured, 
        skipkeys=True, 
        ensure_ascii=False, 
        check_circular=True,
        allow_nan=True,
        indent=2,
        separators=None,
        default=None,
        sort_keys=False,
    )
    return serial


T1 = typing.TypeVar('T1')

def from_json(s, type:typing.Type[T1]|None = None) -> T1:
    unstructured = json.loads(s)
    if type is None:
        return unstructured
    else:
        obj = json_converter.structure(unstructured, type)
        return obj
    
format_json = SerializationFormat(
    serialize=to_json,
    deserialize=from_json,
    extensions=('.json',)
)
    

def to_tsv(items) -> str:
    fieldnames = {}
    rows = []    
    for item in items:
        unstructured = json_converter.unstructure(item)
        rows.append({k: json.dumps(v) for k, v in unstructured.items()})
        fieldnames.update(dict.fromkeys(unstructured))
    buffer = io.StringIO()
    writer = csv.DictWriter(
        f=buffer,
        fieldnames=fieldnames,
        restval=None,
        extrasaction="ignore",
        delimiter='\t',
        quotechar=None,
        escapechar="\\",
        doublequote=False,
        skipinitialspace=True,
        lineterminator="\n",
        quoting=csv.QUOTE_NONE,
        strict=True,
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


T2 = typing.TypeVar('T2')

def from_tsv(
    s,
    type: typing.Type[T2] = None
) -> T2:
    buffer = io.StringIO(s)
    reader = csv.DictReader(
        f=buffer,
        restval=None,
        delimiter='\t',
        quotechar=None,
        escapechar="\\",
        doublequote=False,
        skipinitialspace=True,
        lineterminator="\n",
        quoting=csv.QUOTE_NONE,
    )
    rows = ({field: json.loads(cell) for field, cell in row.items()} for row in reader)
    if type is None:
        return list(rows)
    else:
        item_type, *_ = typing.get_args(type)
        records = type(json_converter.structure(row, item_type) for row in rows)
        return records
    

format_tsv = SerializationFormat(
    serialize=to_tsv,
    deserialize=from_tsv,
    binary=False,
    extensions=('.tsv',)
)


json_converter = cjson.make_converter()
json_converter.register_unstructure_hook(Path, str)
json_converter.register_structure_hook(Path, lambda v, _: Path(v))
json_converter.register_unstructure_hook(File, str)
json_converter.register_unstructure_hook(File, lambda v, _: File(v))


if __name__ == '__main__':


    from attrs import define, field

    @define(hash=True)
    class Foo:
        bar: tuple[str,...]
        bat: int
        

    foo = Foo(('hello', 'world'), 2)
    foo_json = to_json(foo)
    print(foo_json)
    foo_copy = from_json(foo_json, Foo)
    print(foo_copy)
    foo_copy.bat = 8382
    foo_copy.bar = ("w\tx\nyz", "lbah")

    file = File('data/foo.json', Foo)
    file.save(foo_copy)
    foo_cpcp = file.load()
    assert foo_cpcp is not foo_copy
    print(f"{foo_cpcp = }")

    from collections import deque

    footsv = File('data/foo.tsv', deque[Foo])
    footsv.save(deque((foo, foo_copy, foo_cpcp)))
    foos = footsv.load()
    print(f"{foos = }")

    for foo in foos:
        print(foo)
