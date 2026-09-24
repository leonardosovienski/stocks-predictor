"""Make `conformance.fixtures` importable both in the repository and in the cleanroom tree."""
import pathlib
import sys

TESTS = str(pathlib.Path(__file__).resolve().parents[1])
if TESTS not in sys.path:
    sys.path.insert(0, TESTS)
