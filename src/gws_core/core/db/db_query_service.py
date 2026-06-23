"""Service for running read-only SQL queries against a brick database.

This holds the logic behind the ``gws db query`` / ``gws db list`` CLI commands,
separated from the CLI so it can be unit-tested without typer. The service is
deliberately free of any CLI concern: it validates and runs queries and raises
:class:`DbQueryError` on misuse, leaving argument parsing, environment
initialization and output formatting to the caller.

Safety model (matches the CLI's intent):

- Only read-only statements are accepted (SELECT/SHOW/EXPLAIN/DESCRIBE/WITH).
  Anything else, or stacked statements, are rejected before execution.
- Every query runs inside a transaction that is always rolled back, so nothing
  is ever persisted even if the read-only guard is somehow bypassed.
"""

import re
from dataclasses import dataclass

from gws_core.core.db.abstract_db_manager import AbstractDbManager


class DbQueryError(Exception):
    """Raised when a query is rejected or cannot be run.

    The message is user/agent-readable and includes a concrete next action so
    the caller can surface it directly.
    """


@dataclass
class DbQueryResult:
    """Result of a read-only query.

    :param columns: Column names in result order.
    :param rows: All rows returned (before any display limit is applied).
    """

    columns: list[str]
    rows: list[tuple]

    def row_count(self) -> int:
        return len(self.rows)

    def limited_rows(self, limit: int) -> tuple[list[tuple], bool]:
        """Return the rows capped to ``limit`` and whether truncation occurred.

        :param limit: Max rows to keep. ``0`` (or falsy) means no limit.
        :return: Tuple of (rows, truncated).
        """
        if not limit or len(self.rows) <= limit:
            return self.rows, False
        return self.rows[:limit], True


class DbQueryService:
    """Read-only SQL access to brick databases.

    All methods are classmethods/staticmethods: the service holds no state, it
    just operates on the DbManager singletons that are already registered.
    """

    # Statements that only read data. Anything else is rejected.
    ALLOWED_STARTS = ("select", "show", "explain", "describe", "desc", "with")

    # Mutating keywords. Rejected even if the statement starts with an allowed
    # keyword (e.g. a CTE wrapping an INSERT, or stacked statements).
    FORBIDDEN_KEYWORDS = (
        "insert", "update", "delete", "drop", "alter", "create", "truncate",
        "replace", "rename", "grant", "revoke", "lock", "unlock", "set",
        "call", "load", "commit", "rollback", "savepoint", "merge", "do",
        "handler", "install", "uninstall", "flush", "reset", "shutdown",
    )

    @staticmethod
    def _strip_sql(sql: str) -> str:
        """Remove comments and trailing semicolons so the guard can't be fooled."""
        sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)  # /* block */ comments
        sql = re.sub(r"(--|#)[^\n]*", " ", sql)  # -- and # line comments
        return sql.strip().rstrip(";").strip()

    @classmethod
    def assert_read_only(cls, sql: str) -> None:
        """Raise :class:`DbQueryError` if ``sql`` is not a single read-only query.

        :param sql: The raw SQL provided by the caller.
        :raises DbQueryError: If the statement is empty, stacked, starts with a
            non-read-only keyword, or contains a mutating keyword.
        """
        cleaned = cls._strip_sql(sql)

        if not cleaned:
            raise DbQueryError("empty SQL statement. Provide a SELECT/SHOW/DESCRIBE query.")

        if ";" in cleaned:
            raise DbQueryError(
                "multiple statements are not allowed. Run a single read-only query "
                "(no ';' separators)."
            )

        lowered = cleaned.lower()
        first_word = re.split(r"\s+", lowered, maxsplit=1)[0]

        if first_word not in cls.ALLOWED_STARTS:
            raise DbQueryError(
                f"only read-only statements are allowed "
                f"({', '.join(s.upper() for s in cls.ALLOWED_STARTS)}). "
                f"Got '{first_word.upper()}'. This tool cannot modify data."
            )

        for keyword in cls.FORBIDDEN_KEYWORDS:
            if re.search(rf"\b{keyword}\b", lowered):
                raise DbQueryError(
                    f"forbidden keyword '{keyword.upper()}' detected. This tool is "
                    "read-only and cannot modify data."
                )

    @staticmethod
    def get_all_managers() -> list[AbstractDbManager]:
        """Return every registered DbManager instance."""
        return list(AbstractDbManager.get_db_managers())

    @classmethod
    def list_db_names(cls) -> list[str]:
        """Return the sorted brick names of all registered databases."""
        return sorted({m.get_brick_name() for m in cls.get_all_managers()})

    @classmethod
    def resolve_db_manager(cls, db_name: str) -> AbstractDbManager:
        """Find the DbManager whose brick name (or unique name) matches ``db_name``.

        :param db_name: Brick name or unique name of the target database.
        :raises DbQueryError: If no database matches ``db_name``.
        """
        managers = cls.get_all_managers()

        by_key: dict[str, AbstractDbManager] = {}
        for manager in managers:
            by_key[manager.get_brick_name()] = manager
            by_key[manager.get_unique_name()] = manager

        if db_name in by_key:
            return by_key[db_name]

        available = sorted({m.get_brick_name() for m in managers})
        raise DbQueryError(
            f"no database found for '{db_name}'. "
            f"Available: {', '.join(available)}. Run 'gws db list' to see them."
        )

    @classmethod
    def execute_read_only_query(cls, db_name: str, sql: str) -> DbQueryResult:
        """Validate and run a read-only query against the named database.

        The query runs inside a transaction that is always rolled back so
        nothing is ever persisted. Assumes the databases are already
        initialized by the caller (e.g. via the server init path).

        :param db_name: Brick name or unique name of the target database.
        :param sql: The read-only SQL to run.
        :raises DbQueryError: If the SQL is not read-only, the database is
            unknown or not connected, or the query itself fails.
        :return: The columns and rows produced by the query.
        """
        cls.assert_read_only(sql)

        db_manager = cls.resolve_db_manager(db_name)

        if not db_manager.is_initialized():
            raise DbQueryError(
                f"database '{db_name}' could not be connected. Is the lab db reachable? "
                "Try 'gws server run' first."
            )

        db = db_manager.get_db()

        try:
            with db.atomic() as txn:
                cursor = db.execute_sql(sql)
                columns = (
                    [desc[0] for desc in cursor.description] if cursor.description else []
                )
                rows = list(cursor.fetchall())
                txn.rollback()
        except Exception as err:
            raise DbQueryError(f"query failed: {err}") from err

        return DbQueryResult(columns=columns, rows=rows)
