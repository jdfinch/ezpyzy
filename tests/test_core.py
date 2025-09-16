from ezpyzy.core import greet, User, to_dict, from_dict

def test_greet():
    assert "Hello, World" in greet("World")

def test_attrs_cattrs_roundtrip():
    u = User(name="Ava", age=30)
    d = to_dict(u)
    u2 = from_dict(User, d)
    assert u == u2
