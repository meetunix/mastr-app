"""Read-only access to the database of mastr-tool.

The maps page reads all its data (units, operators, EEG plants) directly from
the database. The connection is configured with the same variables as
mastr-tool: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD. Without DB_HOST
the maps page only shows a message.

mastr-tool drops and rebuilds all tables on every import and adds the primary
keys only after all data is loaded. A table without primary key is missing or
still being filled, so ready_columns() reports it as being updated.

The connections are kept in a small pool: a new connection costs several
round trips (TCP, TLS, authentication) and starts with cold caches, a reused
one also reuses the plans of its prepared statements. Idle connections hold
no locks (autocommit), so they don't block the import.
"""

import atexit
import os
import threading
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

DB_HOST = (os.getenv("DB_HOST") or "").strip()

CONNECT_TIMEOUT_SECONDS = 3
# The import drops the tables (exclusive lock); a query must neither wait for
# that nor hold up a worker thread for long.
LOCK_TIMEOUT_MS = 2000
STATEMENT_TIMEOUT_MS = 5000
POOL_MAX_SIZE = 4

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()


class DatabaseUnavailable(Exception):
    """The database can't be queried (not configured, not reachable, ...)."""


class DatabaseUpdating(DatabaseUnavailable):
    """A table is missing or still being imported by mastr-tool."""


def is_configured() -> bool:
    return bool(DB_HOST)


def _get_pool() -> ConnectionPool:
    """The pool, created on first use: in the process that serves the
    requests, not in a parent process (e.g. the reloader of the dev server)."""
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = ConnectionPool(
                kwargs={
                    "host": DB_HOST,
                    "port": os.getenv("DB_PORT") or "5432",
                    "dbname": os.getenv("DB_NAME") or "mastr",
                    "user": os.getenv("DB_USER") or "mastr",
                    "password": os.getenv("DB_PASSWORD") or None,
                    "connect_timeout": CONNECT_TIMEOUT_SECONDS,
                    "application_name": "mastr-app",
                    # read-only, even if the configured role may write;
                    # autocommit, so no transaction stays open (it would block
                    # the import's DROP TABLE)
                    "options": (
                        "-c default_transaction_read_only=on"
                        f" -c lock_timeout={LOCK_TIMEOUT_MS} -c statement_timeout={STATEMENT_TIMEOUT_MS}"
                    ),
                    "autocommit": True,
                    "row_factory": dict_row,
                },
                min_size=1,
                max_size=POOL_MAX_SIZE,
                # how long a request waits for a connection
                timeout=CONNECT_TIMEOUT_SECONDS,
                name="mastr-app",
                open=True,
            )
            atexit.register(_pool.close)
        return _pool


def run[T](work: Callable[[psycopg.Connection], T]) -> T:
    """Run work (read-only queries) with a connection of the pool; rows are
    dicts. Database errors are raised as DatabaseUnavailable.

    If a pooled connection was broken by a database restart, or has a
    prepared statement outdated by a schema change of mastr-tool, the other
    pooled connections are too: all of them are replaced and work runs once
    more with a new connection.
    """
    if not is_configured():
        raise DatabaseUnavailable("no database configured (DB_HOST is not set)")
    try:
        for attempt in (1, 2):
            with _get_pool().connection() as connection:
                try:
                    return work(connection)
                except (psycopg.OperationalError, psycopg.errors.FeatureNotSupported) as e:
                    outdated = connection.broken or isinstance(e, psycopg.errors.FeatureNotSupported)
                    if attempt == 2 or not outdated:
                        raise
                    connection.close()
            _get_pool().drain()
        raise AssertionError("unreachable")
    except psycopg.Error as e:
        raise DatabaseUnavailable(str(e).strip()) from e


def ready_columns(connection: psycopg.Connection, tables: list[str]) -> dict[str, set[str]]:
    """The column names of the given tables. Raises DatabaseUpdating if one of
    them is missing or still being imported (has no primary key yet)."""
    rows = connection.execute(
        "SELECT c.relname, a.attname FROM pg_class c JOIN pg_attribute a ON a.attrelid = c.oid "
        "WHERE c.oid IN (SELECT to_regclass(t) FROM unnest(%s::text[]) t) AND a.attnum > 0 AND NOT a.attisdropped "
        "AND EXISTS (SELECT FROM pg_constraint k WHERE k.conrelid = c.oid AND k.contype = 'p')",
        (tables,),
    ).fetchall()
    columns: dict[str, set[str]] = {}
    for row in rows:
        columns.setdefault(row["relname"], set()).add(row["attname"])
    not_ready = [table for table in tables if table not in columns]
    if not_ready:
        raise DatabaseUpdating(f"tables missing or being imported: {', '.join(not_ready)}")
    return columns


def as_export_text(value: Any) -> str:
    """A database value as text, as it appears in the CSV exports: empty for
    NULL, 'ja'/'nein' for booleans, ISO format for dates and timestamps."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "ja" if value else "nein"
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)
