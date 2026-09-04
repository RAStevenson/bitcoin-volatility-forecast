"""Every module, class, and function in src/ and scripts/ carries a
docstring. Presence only; the form rules are a review matter."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRS = ("src", "scripts")


def _bare_definitions(path):
    """Return one 'file:line kind name' string per undocumented module,
    class, or function in the file at path."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    rel = path.relative_to(ROOT).as_posix()
    found = []
    if ast.get_docstring(tree) is None:
        found.append(f"{rel}:1 module")
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
            continue
        if ast.get_docstring(node) is None:
            kind = "class" if isinstance(node, ast.ClassDef) else "def"
            found.append(f"{rel}:{node.lineno} {kind} {node.name}")
    return found


def test_every_definition_is_documented():
    bare = [line for d in SOURCE_DIRS
            for path in sorted((ROOT / d).rglob("*.py"))
            for line in _bare_definitions(path)]
    assert not bare, ("undocumented definitions:\n  "
                      + "\n  ".join(bare))
