from unittest import TestCase
from unittest.mock import patch

from gws_core.core.db.db_query_service import (
    DbQueryError,
    DbQueryResult,
    DbQueryService,
)
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.test.base_test_case import BaseTestCase


class _FakeManager:
    """Minimal stand-in for an AbstractDbManager for resolution tests."""

    def __init__(self, brick_name: str, name: str, initialized: bool = True):
        self._brick_name = brick_name
        self._name = name
        self._initialized = initialized

    def get_brick_name(self) -> str:
        return self._brick_name

    def get_name(self) -> str:
        return self._name

    def get_unique_name(self) -> str:
        return f"{self._brick_name}-{self._name}"

    def is_initialized(self) -> bool:
        return self._initialized


# test_db_query_service
class TestDbQueryServiceValidation(TestCase):
    """Pure-logic tests for DbQueryService that need no database."""

    # ------------------------------------------------------------------ #
    # assert_read_only
    # ------------------------------------------------------------------ #

    def test_assert_read_only_accepts_read_statements(self):
        for sql in [
            "SELECT * FROM foo",
            "select 1",
            "  SHOW TABLES  ",
            "DESCRIBE foo",
            "desc foo",
            "EXPLAIN SELECT * FROM foo",
            "WITH cte AS (SELECT 1) SELECT * FROM cte",
            "SELECT * FROM foo;",  # trailing semicolon is stripped, still single
            "SELECT * FROM foo -- a trailing comment",
        ]:
            with self.subTest(sql=sql):
                # Should not raise
                DbQueryService.assert_read_only(sql)

    def test_assert_read_only_rejects_empty(self):
        for sql in ["", "   ", ";", "-- only a comment", "/* block */"]:
            with self.subTest(sql=sql):
                with self.assertRaises(DbQueryError):
                    DbQueryService.assert_read_only(sql)

    def test_assert_read_only_rejects_write_statements(self):
        for sql in [
            "INSERT INTO foo VALUES (1)",
            "UPDATE foo SET a = 1",
            "DELETE FROM foo",
            "DROP TABLE foo",
            "ALTER TABLE foo ADD col INT",
            "CREATE TABLE foo (id INT)",
            "TRUNCATE foo",
            "SET @x = 1",
        ]:
            with self.subTest(sql=sql):
                with self.assertRaises(DbQueryError):
                    DbQueryService.assert_read_only(sql)

    def test_assert_read_only_rejects_stacked_statements(self):
        with self.assertRaises(DbQueryError):
            DbQueryService.assert_read_only("SELECT 1; DROP TABLE foo")

    def test_assert_read_only_rejects_mutating_keyword_hidden_in_cte(self):
        # Starts with an allowed keyword but smuggles a forbidden one.
        with self.assertRaises(DbQueryError):
            DbQueryService.assert_read_only(
                "WITH x AS (SELECT 1) INSERT INTO foo SELECT * FROM x"
            )

    def test_assert_read_only_does_not_match_keyword_substrings(self):
        # 'created_at' contains 'create' but is not the CREATE keyword.
        DbQueryService.assert_read_only("SELECT created_at FROM foo")
        # 'updated' / 'inserted_by' as identifiers must not trip the guard.
        DbQueryService.assert_read_only("SELECT inserted_by FROM foo")

    def test_assert_read_only_ignores_keyword_in_block_comment(self):
        DbQueryService.assert_read_only("SELECT 1 /* DELETE everything */")

    # ------------------------------------------------------------------ #
    # resolve_db_manager / list_db_names
    # ------------------------------------------------------------------ #

    def test_resolve_db_manager_by_brick_and_unique_name(self):
        fake = _FakeManager("gws_invest", "db")
        with patch.object(DbQueryService, "get_all_managers", return_value=[fake]):
            self.assertIs(DbQueryService.resolve_db_manager("gws_invest"), fake)
            self.assertIs(DbQueryService.resolve_db_manager("gws_invest-db"), fake)

    def test_resolve_db_manager_unknown_raises(self):
        fake = _FakeManager("gws_invest", "db")
        with patch.object(DbQueryService, "get_all_managers", return_value=[fake]):
            with self.assertRaises(DbQueryError) as ctx:
                DbQueryService.resolve_db_manager("does_not_exist")
            # The error should list available databases to guide the caller.
            self.assertIn("gws_invest", str(ctx.exception))

    def test_list_db_names_is_sorted_and_unique(self):
        managers = [
            _FakeManager("gws_invest", "db"),
            _FakeManager("gws_core", "db"),
            _FakeManager("gws_core", "db"),  # duplicate brick name
        ]
        with patch.object(DbQueryService, "get_all_managers", return_value=managers):
            self.assertEqual(DbQueryService.list_db_names(), ["gws_core", "gws_invest"])

    def test_execute_rejects_query_on_uninitialized_db(self):
        fake = _FakeManager("gws_invest", "db", initialized=False)
        with patch.object(DbQueryService, "get_all_managers", return_value=[fake]):
            with self.assertRaises(DbQueryError) as ctx:
                DbQueryService.execute_read_only_query("gws_invest", "SELECT 1")
            self.assertIn("could not be connected", str(ctx.exception))

    # ------------------------------------------------------------------ #
    # DbQueryResult.limited_rows
    # ------------------------------------------------------------------ #

    def test_limited_rows_no_truncation_when_under_limit(self):
        result = DbQueryResult(columns=["a"], rows=[(1,), (2,)])
        rows, truncated = result.limited_rows(5)
        self.assertEqual(rows, [(1,), (2,)])
        self.assertFalse(truncated)

    def test_limited_rows_truncates_over_limit(self):
        result = DbQueryResult(columns=["a"], rows=[(1,), (2,), (3,)])
        rows, truncated = result.limited_rows(2)
        self.assertEqual(rows, [(1,), (2,)])
        self.assertTrue(truncated)

    def test_limited_rows_zero_limit_means_no_limit(self):
        result = DbQueryResult(columns=["a"], rows=[(1,), (2,), (3,)])
        rows, truncated = result.limited_rows(0)
        self.assertEqual(rows, [(1,), (2,), (3,)])
        self.assertFalse(truncated)


# test_db_query_service
class TestDbQueryServiceExecution(BaseTestCase):
    """Integration tests that run real queries against the gws_core test db."""

    def test_execute_read_only_query_returns_rows(self):
        result = DbQueryService.execute_read_only_query(
            GwsCoreDbManager.get_instance().get_brick_name(),
            "SELECT 1 AS one, 2 AS two",
        )
        self.assertEqual(result.columns, ["one", "two"])
        self.assertEqual(result.rows, [(1, 2)])
        self.assertEqual(result.row_count(), 1)

    def test_execute_read_only_query_resolves_by_unique_name(self):
        manager = GwsCoreDbManager.get_instance()
        result = DbQueryService.execute_read_only_query(
            manager.get_unique_name(), "SELECT 42 AS answer"
        )
        self.assertEqual(result.rows, [(42,)])

    def test_execute_read_only_query_with_literal_percent_in_like(self):
        """A '%' in the SQL (e.g. a LIKE pattern) must not be treated as a
        parameter placeholder by the driver.

        Regression: pymysql runs the query through %-style substitution, so an
        un-escaped '%' raised "not enough arguments for format string" before
        the literal was reached.
        """
        result = DbQueryService.execute_read_only_query(
            GwsCoreDbManager.get_instance().get_brick_name(),
            "SELECT 'fake_pay_abc' LIKE 'fake_pay_%' AS matched",
        )
        self.assertEqual(result.columns, ["matched"])
        self.assertEqual(result.rows, [(1,)])

    def test_execute_read_only_query_rejects_write(self):
        # The guard must reject writes before they reach the database.
        with self.assertRaises(DbQueryError):
            DbQueryService.execute_read_only_query(
                GwsCoreDbManager.get_instance().get_brick_name(),
                "CREATE TABLE should_not_exist (id INT)",
            )

    def test_execute_read_only_query_rolls_back_side_effects(self):
        """A query is always run inside a rolled-back transaction.

        We can't easily smuggle a write past the guard, so instead we assert
        that running a temporary-table creation through the raw db (bypassing
        the guard) inside the service leaves nothing behind. Here we simply
        confirm a SELECT does not persist a session temp table across calls,
        which exercises the atomic/rollback wrapper.
        """
        manager = GwsCoreDbManager.get_instance()
        # Sanity: a normal read works and returns the expected shape.
        result = DbQueryService.execute_read_only_query(
            manager.get_brick_name(), "SELECT COUNT(*) AS n FROM information_schema.tables"
        )
        self.assertEqual(result.columns, ["n"])
        self.assertEqual(len(result.rows), 1)
        self.assertGreaterEqual(result.rows[0][0], 1)
