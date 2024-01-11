"""
Cache solves the problem of avoiding re-loading the same file multiple times.

Each file is loaded only once, and the content is cached in memory.
"""


from ezpyzy.file import File, filelike, formatlike
import ezpyzy.format as fmt

import pathlib
import dataclasses
import datetime

import typing as T


class Caches:

    def __init__(self):
        self.entries: dict[pathlib.Path, CacheEntry] = {}

    def read(self, path_or_file: filelike):
        file = File(path_or_file)
        path = file.path
        last_disk_modify_time = file.modified_time()
        if path in self.entries:
            entry: CacheEntry = self.entries[path]
            if entry.cache_content_is_valid():
                content = entry.content
            else:
                content = entry.file.read()
                entry.content = content
                entry.accessed_time = datetime.datetime.now()
                entry.modified_time = last_disk_modify_time
        else:
            content = file.read()
            entry = CacheEntry(
                file=file,
                content=content,
                accessed_time=datetime.datetime.now(),
                modified_time=last_disk_modify_time
            )
            self.entries[path] = entry
        return content

    def write(self, path_or_file: filelike, content: str | bytes):
        file = File(path_or_file)
        path = file.path
        if path in self.entries:
            entry = self.entries[path]
            entry.file.write(content)
            entry.content = content
            entry.accessed_time = datetime.datetime.now()
            entry.modified_time = entry.accessed_time
        else:
            file.write(content)
            write_time = datetime.datetime.now()
            self.entries[path] = CacheEntry(
                file=file,
                content=content,
                accessed_time=write_time,
                modified_time=write_time
            )

    def load(self,
        path_or_file: filelike,
        format: formatlike=None,
        *args, **kwargs
    ):
        file = File(path_or_file, format)
        format = file.format
        path = file.path
        if path in self.entries and self.entries[path].cache_deserialized_is_valid(format):
            entry = self.entries[path]
            return entry.deserialized
        else:
            serialized = self.read(file)
            deserialized = format.deserialize(serialized, *args, **kwargs) # noqa
            entry = self.entries[path]
            entry.deserialized = deserialized
            entry.deserialized_format = format
            entry.deserialized_time = datetime.datetime.now()
            return deserialized

    def save(self,
        path_or_file: filelike,
        obj,
        format: formatlike=None,
        *args, **kwargs
    ):
        file = File(path_or_file, format)
        path = file.path
        format = file.format
        serialized = format.serialize(obj, *args, **kwargs) # noqa
        self.write(file, serialized)
        entry = self.entries[path]
        entry.deserialized = obj
        entry.deserialized_format = format
        entry.deserialized_time = datetime.datetime.now()

    def clear(self, *paths_or_files: filelike):
        if not paths_or_files:
            self.entries.clear()
        else:
            for path in paths_or_files:
                path = File(path).path
                if path in self.entries:
                    del self.entries[path]

    def cached(self, targets: T.Iterable[filelike], sources: T.Iterable[filelike] = ()):
        targets = [Cache(target) for target in targets]
        if all(target.path.exists() for target in targets):
            earliest_target = min(target.modified_time() for target in targets)
            sources = [Cache(source) for source in sources]
            if all(source.path.exists() for source in sources):
                if all(source.modified_time() < earliest_target for source in sources):
                    if len(targets) == 1:
                        return targets[0].load()
                    else:
                        return tuple(target.load() for target in targets)
        return None



@dataclasses.dataclass
class CacheEntry:
    file: File
    content: str | bytes = None
    accessed_time: datetime.datetime = None
    modified_time: datetime.datetime = None
    deserialized: T.Any = None
    deserialized_time: datetime.datetime = None
    deserialized_format: type[fmt.Savable] = None

    def cache_content_is_valid(self):
        return (
            self.accessed_time and self.modified_time and
            self.accessed_time >= self.file.modified_time()
        )

    def cache_deserialized_is_valid(self, format:type[fmt.Savable]=None):
        return(
            self.cache_content_is_valid() and
            self.deserialized_time and
            self.deserialized_format is format and
            self.deserialized_time >= self.file.modified_time()
        )

    def __str__(self):
        return f'CacheEntry({self.file.path}, last read = {self.accessed_time or "never"})'



class Cache(File):

    caches = Caches()

    def read(self, n=None):
        if n is None:
            content = self.caches.read(self.path)
        else:
            content = File.read(self, n)
        return content

    def load(self, *args, **kwargs):
        return self.caches.load(self.path, format=self.format, *args, **kwargs)

    def write(self, content, start=0):
        if start == 0:
            self.caches.write(self.path, content)
        else:
            File.write(self, content, start=start)
            self.caches.clear(self.path)

    def save(self, obj, *args, **kwargs):
        if not args and not kwargs:
            self.caches.save(self.path, obj, format=self.format, *args, **kwargs)
        else:
            File.save(self, obj, *args, **kwargs)

    def modified_time(self):
        file_modified_time = File.modified_time(self)
        cache_enty = self.caches.entries.get(self.path)
        if cache_enty:
            cache_modified_time = cache_enty.modified_time
            if cache_modified_time:
                return max(file_modified_time, cache_modified_time)
        return file_modified_time

    def accessed_time(self):
        file_accessed_time = File.accessed_time(self)
        cache_enty = self.caches.entries.get(self.path)
        if cache_enty:
            cache_accessed_time = cache_enty.accessed_time
            if cache_accessed_time:
                return max(cache_accessed_time, file_accessed_time)
        return file_accessed_time

    def cached(self, sources: T.Iterable[filelike] = ()):
        return self.caches.cached([self], sources=sources)


caches = Cache.caches

