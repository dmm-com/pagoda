"""SQLite backend tuned to behave like Pagoda's MySQL, for lite dev mode.

Running the suite on stock SQLite passes ~99.7% of it. The residue is not
random: it is two places where Django's SQLite backend declares *fewer*
constraints than MySQL does, so code that is correct under MySQL silently
behaves differently.

1. **Integer ranges.** Django derives ``max_value``/``min_value`` validators
   from ``integer_field_range()``. The SQLite backend reports the full 64-bit
   range, so an ``IntegerField`` accepts values that MySQL rejects and the API
   returns a different validation error. Restoring the base (ANSI/MySQL)
   ranges makes the validators identical on both backends.

2. **Case-insensitive text.** Pagoda's MySQL runs a ``_ci`` collation, so
   ``name="lb"`` finds ``"LB"`` and unique constraints on names fold case.
   SQLite compares text case-sensitively by default. Declaring text columns
   ``COLLATE NOCASE`` reproduces that for equality, uniqueness and ordering.

   MySQL's ``REGEXP`` takes its case sensitivity from the same collation, so
   ``name__regex="^entity-"`` matches ``"Entity-1"`` there and would not here.
   Django implements ``__iregex`` by prefixing the pattern with ``(?i)``;
   applying that to ``__regex`` too makes the two backends agree.

``NOCASE`` only folds ASCII, where a ``utf8mb4_*_ci`` collation folds much
more, so this narrows the gap rather than closing it. JSON columns are left
alone deliberately -- JSON keys are case-sensitive.
"""

from typing import Any

from django.db.backends.base.operations import BaseDatabaseOperations
from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper
from django.db.backends.sqlite3.operations import DatabaseOperations as SQLiteDatabaseOperations

#: Text field types that MySQL would store under a case-insensitive collation.
_CASE_INSENSITIVE_TYPES = (
    "CharField",
    "TextField",
    "SlugField",
    "FilePathField",
    "FileField",
    "EmailField",
)


class DatabaseOperations(SQLiteDatabaseOperations):
    def integer_field_range(self, internal_type: str) -> tuple[int, int]:
        # Skip the SQLite override that widens every integer to 64 bits.
        return BaseDatabaseOperations.integer_field_range(self, internal_type)


def _collated(data_type: Any) -> Any:
    if callable(data_type):
        return lambda data: "%s COLLATE NOCASE" % data_type(data)
    return "%s COLLATE NOCASE" % data_type


class DatabaseWrapper(SQLiteDatabaseWrapper):
    ops_class = DatabaseOperations

    # Match MySQL, where REGEXP follows the column's case-insensitive
    # collation. This is the spelling Django already uses for __iregex.
    operators = {
        **SQLiteDatabaseWrapper.operators,
        "regex": "REGEXP '(?i)' || %s",
    }

    data_types = {
        **SQLiteDatabaseWrapper.data_types,
        **{
            name: _collated(SQLiteDatabaseWrapper.data_types[name])
            for name in _CASE_INSENSITIVE_TYPES
            if name in SQLiteDatabaseWrapper.data_types
        },
    }
