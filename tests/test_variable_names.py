"""Every name bound in src/, scripts/, and tests/ says what it holds:
no one- or two-character variable, parameter, loop variable, exception
name, or instance attribute outside a closed list of conventions."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = ("src", "scripts", "tests")
# X and y: a model's input matrix and target. ax: one matplotlib axes.
# i, j: an integer loop counter. Nothing else is allowed short.
ALLOWED_SHORT = {"X", "y", "ax", "i", "j"}


def _bound_names(tree):
    """Yield (line, name) for every name the tree binds: assignment and
    loop targets, function and lambda arguments, exception names, and
    attributes assigned on self."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            yield node.lineno, node.id
        elif isinstance(node, ast.arg):
            yield node.lineno, node.arg
        elif isinstance(node, ast.ExceptHandler) and node.name:
            yield node.lineno, node.name
        elif (isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store)
              and isinstance(node.value, ast.Name) and node.value.id == "self"):
            yield node.lineno, node.attr


def _short_names(path):
    """Return one 'file:line name' string per short name bound in the
    file at path that is not on the allowed list."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    rel = path.relative_to(ROOT).as_posix()
    found = set()
    for line, name in _bound_names(tree):
        core = name.strip("_")
        if core and len(core) <= 2 and core not in ALLOWED_SHORT:
            found.add((line, name))
    return [f"{rel}:{line} {name}" for line, name in sorted(found)]


def test_every_name_says_what_it_holds():
    short = [entry for folder in SOURCE_DIRS
             for path in sorted((ROOT / folder).rglob("*.py"))
             for entry in _short_names(path)]
    assert not short, ("short names (python-repo-layout, variable names):\n  "
                       + "\n  ".join(short))
