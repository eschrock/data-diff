from typing import Tuple, Iterator, Optional

from .database import connect_to_uri
from .diff_tables import (
    TableSegment,
    TableDiffer,
    DEFAULT_BISECTION_THRESHOLD,
    DEFAULT_BISECTION_FACTOR,
    DbKey,
    DbTime,
    parse_table_name,
)


class TableRef:
    """Connects to a URI and creates a table ref

    This is an auxiliary class for diff_tables()
    """

    def __init__(self, db_uri: str, table_name: str):
        self.db = connect_to_uri(db_uri)
        self.table_name = table_name

    def create_table_segment(self, **kwargs):
        return TableSegment(self.db, parse_table_name(self.table_name), **kwargs)


def diff_tables(
    table1: TableRef,
    table2: TableRef,
    *,
    # Name of the key column, which uniquely identifies each row (usually id)
    key_column: str = "id",
    # Name of updated column, which signals that rows changed (usually updated_at or last_update)
    update_column: str = None,
    # Extra columns to compare
    extra_columns: Tuple[str, ...] = (),
    # Start/end key_column values, used to restrict the segment
    min_key: DbKey = None,
    max_key: DbKey = None,
    # Start/end update_column values, used to restrict the segment
    min_update: DbTime = None,
    max_update: DbTime = None,
    # Into how many segments to bisect per iteration
    bisection_factor: int = DEFAULT_BISECTION_FACTOR,
    # When should we stop bisecting and compare locally (in row count)
    bisection_threshold: int = DEFAULT_BISECTION_THRESHOLD,
    # Enable/disable threaded diffing. Needed to take advantage of database threads.
    threaded: bool = True,
    # Maximum size of each threadpool. None = auto. Only relevant when threaded is True.
    # There may be many pools, so number of actual threads can be a lot higher.
    max_threadpool_size: Optional[int] = 1,
    # Enable/disable debug prints
    debug: bool = False,
) -> Iterator:
    """Efficiently finds the diff between table1 and table2.

    Example:
        >>> table1 = TableRef('postgres:///', 'Rating')
        >>> list(diff_tables(table1, table1))
        []

    """
    tables = [table1, table2]
    segments = [
        t.create_table_segment(
            key_column=key_column,
            update_column=update_column,
            extra_columns=extra_columns,
            min_key=min_key,
            max_key=max_key,
            min_updated=min_updated,
            max_updated=max_updated,
        )
        for t in tables
    ]

    differ = TableDiffer(
        bisection_factor=bisection_factor,
        bisection_threshold=bisection_threshold,
        debug=debug,
        threaded=threaded,
        max_threadpool_size=max_threadpool_size,
    )
    return differ.diff_tables(*segments)
