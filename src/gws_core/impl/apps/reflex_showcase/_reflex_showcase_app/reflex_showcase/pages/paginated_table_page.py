"""Paginated table component demo page for the Reflex showcase app."""

import pandas as pd
import reflex as rx
from gws_reflex_main import PaginatedTableState, paginated_table_component

from ..components import example_tabs, page_layout

TOTAL_DEMO_ROWS = 137


def _build_row(i: int) -> dict:
    return {
        "id": i + 1,
        "name": f"Item {i + 1}",
        "category": ["A", "B", "C", "D"][i % 4],
        "value": round((i * 3.14) % 100, 2),
        "in_stock": bool(i % 2),
    }


class DataEditorTableState(PaginatedTableState, rx.State):
    """Paginated table state feeding an ``rx.data_editor``.

    Simulates a server-side data source by slicing a generated range on
    demand — only the current page is materialized into a DataFrame.
    """

    async def fetch_page(self, page: int, page_size: int) -> tuple[pd.DataFrame, int]:
        start = page * page_size
        end = min(start + page_size, TOTAL_DEMO_ROWS)
        rows = [_build_row(i) for i in range(start, end)]
        return pd.DataFrame(rows), TOTAL_DEMO_ROWS

    @rx.var
    def data_editor_columns(self) -> list[dict]:
        df = self.paginated_table
        if df.empty:
            return []
        return [{"title": str(col), "type": "str"} for col in df.columns]

    @rx.var
    def data_editor_rows(self) -> list[list[str]]:
        df = self.paginated_table
        if df.empty:
            return []
        return [
            [("" if pd.isna(v) else str(v)) for v in row]
            for row in df.itertuples(index=False, name=None)
        ]

    @rx.event
    async def load_demo_data(self):
        self.page = 0
        await self.refresh()


def _data_editor_grid() -> rx.Component:
    """Build the ``rx.data_editor`` bound to the paginated state."""
    return rx.box(
        rx.data_editor(
            columns=DataEditorTableState.data_editor_columns,
            data=DataEditorTableState.data_editor_rows,
            row_height=32,
        ),
        width="100%",
        height="420px",
        overflow="hidden",
    )


def paginated_table_page() -> rx.Component:
    """Render the paginated table component demo page."""

    example_component = rx.vstack(
        rx.button(
            "Load demo data",
            on_click=DataEditorTableState.load_demo_data,
            variant="soft",
        ),
        rx.cond(
            DataEditorTableState.has_data,
            rx.box(
                paginated_table_component(
                    grid=_data_editor_grid(),
                    state_cls=DataEditorTableState,
                ),
                width="100%",
                height="480px",
                border="1px solid var(--gray-a5)",
                border_radius="6px",
                overflow="hidden",
            ),
            rx.text(
                "Click the button above to load sample data.",
                color="gray",
                size="2",
            ),
        ),
        align="start",
        width="100%",
        spacing="3",
    )

    code = """import pandas as pd
import reflex as rx
from gws_reflex_main import PaginatedTableState, paginated_table_component


class DataEditorTableState(PaginatedTableState, rx.State):

    async def fetch_page(self, page: int, page_size: int) -> tuple[pd.DataFrame, int]:
        # Replace with a DB query / API call sliced by offset + limit.
        offset = page * page_size
        rows, total = my_data_source.load(offset=offset, limit=page_size)
        return pd.DataFrame(rows), total

    @rx.var
    def data_editor_columns(self) -> list[dict]:
        df = self.paginated_table
        if df.empty:
            return []
        return [{"title": str(c), "type": "str"} for c in df.columns]

    @rx.var
    def data_editor_rows(self) -> list[list[str]]:
        df = self.paginated_table
        if df.empty:
            return []
        return [
            [("" if pd.isna(v) else str(v)) for v in row]
            for row in df.itertuples(index=False, name=None)
        ]

    @rx.event
    async def load_demo_data(self):
        self.page = 0
        await self.refresh()


def my_page() -> rx.Component:
    grid = rx.data_editor(
        columns=DataEditorTableState.data_editor_columns,
        data=DataEditorTableState.data_editor_rows,
    )
    return paginated_table_component(grid=grid, state_cls=DataEditorTableState)
"""

    compatibility_note = rx.callout(
        rx.vstack(
            rx.text(
                "The paginated_table_component is grid-agnostic.",
                weight="bold",
            ),
            rx.text(
                "PaginatedTableState slices the DataFrame and exposes the current page "
                "via the paginated_table var. The wrapper only renders the grid you pass "
                "in, then the pagination_controls bound to the state class — so it works "
                "with any table component, as long as you feed it columns and row data "
                "derived from paginated_table.",
                size="2",
            ),
            rx.text("Supported grids:", weight="bold", margin_top="0.5em"),
            rx.unordered_list(
                rx.list_item(
                    rx.text.strong("rx.data_editor"),
                    " — Glide Data Grid. Expects ",
                    rx.code("columns"),
                    " as ",
                    rx.code("list[dict]"),
                    " with ",
                    rx.code("title"),
                    "/",
                    rx.code("type"),
                    ", and ",
                    rx.code("data"),
                    " as a 2D list of cell values (shown in this demo).",
                ),
                rx.list_item(
                    rx.text.strong("rx._data_table"),
                    " — simple pandas-backed table. Pass ",
                    rx.code("data=state.paginated_table"),
                    " directly; it reads a DataFrame. Uses MUI DataGrid under the hood.",
                ),
                rx.list_item(
                    rx.text.strong("rx.table"),
                    " — low-level Radix table. Build header/body from the DataFrame manually "
                    "(usually with ",
                    rx.code("rx.foreach"),
                    " over a ",
                    rx.code("list[dict]"),
                    " var).",
                ),
                rx.list_item(
                    rx.text.strong("rxe.ag_grid"),
                    " — AG Grid via ",
                    rx.code("reflex-enterprise"),
                    ". The base state already exposes ",
                    rx.code("ag_grid_column_defs"),
                    " and ",
                    rx.code("ag_grid_row_data"),
                    " — wire them to ",
                    rx.code("column_defs"),
                    " and ",
                    rx.code("row_data"),
                    ".",
                ),
            ),
            rx.text(
                "In every case you subclass PaginatedTableState, add vars that reshape "
                "paginated_table into the grid's expected format, and pass the built grid "
                "to paginated_table_component.",
                size="2",
                margin_top="0.5em",
            ),
            spacing="1",
            align="start",
        ),
        icon="info",
        color_scheme="blue",
        width="100%",
        margin_bottom="1em",
    )

    return page_layout(
        "Paginated Table Component",
        "A server-side paginated table wrapper: pass your grid + a PaginatedTableState "
        "subclass and get pagination controls bound for free.",
        compatibility_note,
        example_tabs(
            example_component=example_component,
            code=code,
            title="paginated_table_component with rx.data_editor",
            description="Subclass PaginatedTableState, expose grid-shaped vars derived "
            "from paginated_table, and pass the built grid into the wrapper.",
            func=paginated_table_component,
        ),
    )
