"""Small input contracts shared by entry points and research primitives."""
from datetime import date


def iso_day(value, name='date') -> str:
    if not isinstance(value, str):
        raise ValueError(f'{name} must be a canonical YYYY-MM-DD string')
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f'{name} must be a valid YYYY-MM-DD date') from exc
    if parsed.isoformat() != value:
        raise ValueError(f'{name} must use canonical YYYY-MM-DD format')
    return value


def positive_integer(value, name):
    if type(value) is not int or value < 1:
        raise ValueError(f'{name} must be a positive integer')
    return value
