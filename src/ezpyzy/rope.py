import random as rng
from typing import Optional, Tuple, Union


# ---------- Persistent treap merge & split ----------

def merge(left: Optional["Rope"], right: Optional["Rope"]) -> Optional["Rope"]:
    """Persistent treap merge. Returns new root, inputs unchanged."""
    if left is None:
        return right
    if right is None:
        return left

    # Coalesce if total length fits in one chunk
    if left.length + right.length <= left.segment_size:
        return Rope(str(left) + str(right), segment_size=left.segment_size)

    if left.priority < right.priority:
        new_root = Rope.__new__(Rope)
        new_root.segment_size = left.segment_size
        new_root.content = left.content
        new_root.priority = left.priority
        new_root.left = left.left
        new_root.right = merge(left.right, right)
        new_root.length = ((new_root.left.length if new_root.left else 0)
                           + len(new_root.content)
                           + (new_root.right.length if new_root.right else 0))
        return new_root
    else:
        new_root = Rope.__new__(Rope)
        new_root.segment_size = right.segment_size
        new_root.content = right.content
        new_root.priority = right.priority
        new_root.left = merge(left, right.left)
        new_root.right = right.right
        new_root.length = ((new_root.left.length if new_root.left else 0)
                           + len(new_root.content)
                           + (new_root.right.length if new_root.right else 0))
        return new_root


def split(rope: Optional["Rope"], index: int) -> Tuple[Optional["Rope"], Optional["Rope"]]:
    """Persistent treap split. Returns (L,R), inputs unchanged."""
    if rope is None:
        return None, None

    left_size = rope.left.length if rope.left else 0
    chunk_len = len(rope.content)

    if index < left_size:
        L, new_left = split(rope.left, index)
        new_root = Rope.__new__(Rope)
        new_root.segment_size = rope.segment_size
        new_root.content = rope.content
        new_root.priority = rope.priority
        new_root.left = new_left
        new_root.right = rope.right
        new_root.length = ((new_root.left.length if new_root.left else 0)
                           + chunk_len
                           + (new_root.right.length if new_root.right else 0))
        return L, new_root

    if index > left_size + chunk_len:
        new_right, R = split(rope.right, index - left_size - chunk_len)
        new_root = Rope.__new__(Rope)
        new_root.segment_size = rope.segment_size
        new_root.content = rope.content
        new_root.priority = rope.priority
        new_root.left = rope.left
        new_root.right = new_right
        new_root.length = ((new_root.left.length if new_root.left else 0)
                           + chunk_len
                           + (new_root.right.length if new_root.right else 0))
        return new_root, R

    # Split inside this chunk
    cut_in_chunk = max(0, min(chunk_len, index - left_size))

    L = rope.left
    if cut_in_chunk > 0:
        L = merge(L, Rope(rope.content[:cut_in_chunk], segment_size=rope.segment_size))

    R = rope.right
    if cut_in_chunk < chunk_len:
        R = merge(Rope(rope.content[cut_in_chunk:], segment_size=rope.segment_size), R)

    return L, R


# ---------- Rope class ----------

class Rope:
    def __init__(self, content: str = "", segment_size: int = 1024):
        self.segment_size = segment_size
        self.content = ""
        self.left: Optional["Rope"] = None
        self.right: Optional["Rope"] = None
        self.length = 0
        self.priority = rng.random()

        if content:
            # Safe because __setitem__ fast-paths when total fits
            self[0] = content

    def __len__(self) -> int:
        return self.length

    def __str__(self) -> str:
        left_s = str(self.left) if self.left else ""
        right_s = str(self.right) if self.right else ""
        return left_s + self.content + right_s

    def _swap_fields(self, other: "Rope") -> None:
        (self.segment_size, other.segment_size) = (other.segment_size, self.segment_size)
        (self.content, other.content) = (other.content, self.content)
        (self.left, other.left) = (other.left, self.left)
        (self.right, other.right) = (other.right, self.right)
        (self.length, other.length) = (other.length, self.length)
        (self.priority, other.priority) = (other.priority, self.priority)


    def __iadd__(self, other: "Rope"):
        """Concatenate in place: self := self + other, preserving identity."""
        self[self.length] = other
        return self

    def __getitem__(self, key) -> "Rope":
        """Slice [start:stop], ignoring step. Returns a Rope (nodes shared)."""
        if not isinstance(key, slice):
            raise TypeError("Rope only supports slicing via rope[i:j]")
        start, stop, _ = key.indices(self.length)
        left_tree, mid_plus_right = split(self, start)
        mid_tree, _ = split(mid_plus_right, stop - start)
        return mid_tree if mid_tree else Rope("", segment_size=self.segment_size)

    def __setitem__(self, key: Union[slice, int], value: Union[str, "Rope"]):
        """Insert or replace content at position(s)."""
        if isinstance(key, slice):
            start, stop, _ = key.indices(self.length)
        else:
            start, stop = key, key

        removed = (stop - start)
        added = len(value) if isinstance(value, str) else value.length
        total_length = self.length - removed + added

        # --- coalesce if small enough: string surgery only ---
        if total_length <= self.segment_size:
            base = str(self)
            ins = value if isinstance(value, str) else str(value)
            self.content = base[:start] + ins + base[stop:]
            self.left = None
            self.right = None
            self.length = total_length
            return

        # --- general case: persistent split/merge ---
        insert_rope = value if isinstance(value, Rope) else Rope(value, segment_size=self.segment_size)

        if isinstance(key, slice):
            left_tree, mid_plus_right = split(self, start)
            _, right_tree = split(mid_plus_right, stop - start)
            new_root = merge(merge(left_tree, insert_rope), right_tree)
        else:
            left_tree, right_tree = split(self, start)
            new_root = merge(merge(left_tree, insert_rope), right_tree)

        if new_root is not self and new_root is not None:
            self._swap_fields(new_root)

    def __delitem__(self, key: slice):
        """Delete the half-open slice [start:stop)."""
        if not isinstance(key, slice):
            raise TypeError("Deletion requires a slice, e.g., del rope[i:j]")
        start, stop, _ = key.indices(self.length)

        total_length = self.length - (stop - start)
        if total_length <= self.segment_size:
            base = str(self)
            self.content = base[:start] + base[stop:]
            self.left = None
            self.right = None
            self.length = total_length
            return

        left_tree, mid_plus_right = split(self, start)
        _, right_tree = split(mid_plus_right, stop - start)
        new_root = merge(left_tree, right_tree)
        if new_root is not self and new_root is not None:
            self._swap_fields(new_root)


# ---------- quick sanity check ----------

if __name__ == "__main__":
    r = Rope("abcDEFghi", segment_size=4)
    print("init:", str(r))              # abcDEFghi

    r += Rope("XYZ", segment_size=4)
    print("concat:", str(r))            # abcDEFghiXYZ

    s = r[3:9]
    print("slice:", str(s))             # DEFghi

    r[0] = "<<"
    print("insert:", str(r))            # <<abcDEFghiXYZ

    r[2:5] = "[]"
    print("replace:", str(r))           # <<[]DEFghiXYZ

    del r[2:7]
    print("delete:", str(r))            # <<XYZ
