"""Installed operational entrypoint; legacy experiments require their own commands."""
from .operations import main

if __name__ == '__main__':
    raise SystemExit(main())
