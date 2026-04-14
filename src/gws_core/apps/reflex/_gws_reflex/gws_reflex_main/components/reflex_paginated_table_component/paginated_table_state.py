"""Reusable base state for server-side paginated tables.

Subclass :class:`PaginatedTableState` per table and implement
:meth:`fetch_page` to return the current page's DataFrame and the total row
count. The state only caches the current page slice — the full dataset is
never held in state — so pagination works against DB queries, APIs, or any
other source that can be sliced by offset/limit.

Trigger an initial load (or reload after filters change) with::

    table_state = await self.get_state(MyTableState)
    await table_state.refresh()

Override :meth:`build_column_defs` in a subclass to customize AG Grid column
definitions (pinning, widths, etc.).
"""

from abc import abstractmethod

import pandas as pd
import reflex as rx

PAGE_SIZE_OPTIONS = [25, 50, 100, 200]
DEFAULT_PAGE_SIZE = 50


class PaginatedTableState(rx.State, mixin=True):
    """Base state caching the current page and total row count.

    Subclasses must implement :meth:`fetch_page` to load a single page on
    demand. Every page change (next/prev/first/last/set_page_size) triggers
    a reload, so the underlying data source is responsible for making the
    slice cheap (indexed queries, cached fetches, etc.).
    """

    page: int = 0
    page_size: int = DEFAULT_PAGE_SIZE
    _current_page: pd.DataFrame = pd.DataFrame()
    _total_rows: int = 0

    @abstractmethod
    async def fetch_page(self, page: int, page_size: int) -> tuple[pd.DataFrame, int]:
        """Load a single page of data.

        :param page: Zero-based page index to load.
        :param page_size: Number of rows to return.
        :return: Tuple of (page DataFrame, total row count across all pages).
        """

    @rx.var
    def total_rows(self) -> int:
        return self._total_rows

    @rx.var
    def total_pages(self) -> int:
        if self.page_size <= 0 or self._total_rows == 0:
            return 1
        return (self._total_rows + self.page_size - 1) // self.page_size

    @rx.var
    def page_info(self) -> str:
        if self._total_rows == 0:
            return "0 rows"
        start = self.page * self.page_size + 1
        end = min((self.page + 1) * self.page_size, self._total_rows)
        return f"{start}–{end} of {self._total_rows}"

    @rx.var
    def has_prev(self) -> bool:
        return self.page > 0

    @rx.var
    def has_next(self) -> bool:
        return self.page < self.total_pages - 1

    @rx.var
    def paginated_table(self) -> pd.DataFrame:
        return self._current_page

    @rx.var
    def has_data(self) -> bool:
        return self._total_rows > 0

    def build_column_defs(self, columns: list) -> list[dict]:
        """Build AG Grid column defs from column names. Override for custom styling."""
        return [
            {
                "field": str(col),
                "headerName": str(col),
                "headerTooltip": str(col),
                "resizable": True,
                "sortable": False,
                "filter": False,
            }
            for col in columns
        ]

    @rx.var
    def ag_grid_column_defs(self) -> list[dict]:
        if self._current_page.empty:
            return []
        return self.build_column_defs(list(self._current_page.columns))

    @rx.var
    def ag_grid_row_data(self) -> list[dict]:
        df = self._current_page
        if df.empty:
            return []
        rows = []
        for _, row in df.iterrows():
            rows.append({str(col): ("" if pd.isna(row[col]) else row[col]) for col in df.columns})
        return rows

    async def refresh(self):
        """Reload the current page from :meth:`fetch_page`."""
        df, total = await self.fetch_page(self.page, self.page_size)
        self._current_page = df if df is not None else pd.DataFrame()
        self._total_rows = total

    def clear_table(self):
        self._current_page = pd.DataFrame()
        self._total_rows = 0
        self.page = 0

    @rx.event
    async def next_page(self):
        if self.has_next:
            self.page += 1
            await self.refresh()

    @rx.event
    async def prev_page(self):
        if self.has_prev:
            self.page -= 1
            await self.refresh()

    @rx.event
    async def first_page(self):
        self.page = 0
        await self.refresh()

    @rx.event
    async def last_page(self):
        self.page = max(self.total_pages - 1, 0)
        await self.refresh()

    @rx.event
    async def set_page_size(self, value: str | list[str]):
        raw = value if isinstance(value, str) else value[0]
        try:
            new_size = int(raw)
        except (TypeError, ValueError):
            return
        if new_size <= 0:
            return
        self.page_size = new_size
        self.page = 0
        await self.refresh()
