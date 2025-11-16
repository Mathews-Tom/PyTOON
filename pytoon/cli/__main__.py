"""Enable running pytoon as a module: python -m pytoon.

This module serves as the entry point when PyToon CLI is executed
as a Python module using ``python -m pytoon`` or ``python -m pytoon.cli``.

Example:
    Running the CLI as a module::

        $ python -m pytoon encode data.json -o output.toon
        $ python -m pytoon decode data.toon
        $ python -m pytoon --version
        $ python -m pytoon --help
"""

from __future__ import annotations

import sys

from pytoon.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
