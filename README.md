# ezpyzy

A tiny, friendly Python utility library — **ezpyzy**.

This skeleton uses the modern **`pyproject.toml`** with **hatchling** as the build backend,
a `src/` layout, Ruff for linting, pytest for tests, and an optional pre-commit setup.

## Quick start

```bash
# (Recommended) Use uv or pipx to manage tools
# Install dev extras (ruff, pytest, mypy, pre-commit)
pip install -e ".[dev]"

# Run linters & tests
ruff check .
pytest

# Build the wheel & sdist
python -m build  # needs 'build' package OR use 'hatch build' if you prefer hatch
```

> Note: If you don't have `build` installed: `pip install build`.  
> If you prefer **Hatch** workflows: `pipx install hatch`, then `hatch build` / `hatch test`.

## Usage

```python
from ezpyzy import __version__
from ezpyzy.core import greet, User, to_dict, from_dict

print(__version__)
print(greet("World"))

u = User(name="Ava", age=30)
d = to_dict(u)
print(d)               # {'name': 'Ava', 'age': 30}
print(from_dict(User, d))
```

## Project layout

```
ezpyzy/
├─ src/ezpyzy/
│  ├─ __init__.py
│  └─ core.py
├─ tests/
│  └─ test_core.py
├─ .github/workflows/ci.yml
├─ .pre-commit-config.yaml
├─ pyproject.toml
├─ README.md
├─ LICENSE
└─ .gitignore
```

## Releasing

1. Bump the version in `pyproject.toml` (or use git tags + hatch-vcs if you like).
2. Build: `python -m build` (or `hatch build`).
3. Upload: `twine upload dist/*`.
