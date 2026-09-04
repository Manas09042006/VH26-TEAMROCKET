import ast
from pathlib import Path


def parse_file(filename):
    """
    Read a Python file and convert it into an AST.
    """

    path = Path(filename)

    source = path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source,
        filename=str(path)
    )

    return tree