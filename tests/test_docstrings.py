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
    relative_path = path.relative_to(ROOT).as_posix()
    undocumented = []
    if ast.get_docstring(tree) is None:
        undocumented.append(f"{relative_path}:1 module")
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
            continue
        if ast.get_docstring(node) is None:
            kind = "class" if isinstance(node, ast.ClassDef) else "def"
            undocumented.append(f"{relative_path}:{node.lineno} {kind} {node.name}")
    return undocumented


def test_every_definition_is_documented():
    undocumented = [line for source_dir in SOURCE_DIRS
                    for path in sorted((ROOT / source_dir).rglob("*.py"))
                    for line in _bare_definitions(path)]
    assert not undocumented, ("undocumented definitions:\n  "
                              + "\n  ".join(undocumented))
