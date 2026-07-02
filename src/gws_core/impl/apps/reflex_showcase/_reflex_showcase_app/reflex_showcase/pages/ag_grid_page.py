"""AG Grid component demo page for the Reflex showcase app."""

import reflex as rx
from gws_reflex_main.gws_components import ag_grid_component

from ..components import example_tabs, page_layout

# Small static dataset used by both examples.
_ROWS = [
    {"id": 1, "name": "Alice", "team": "Biology", "score": 92},
    {"id": 2, "name": "Bob", "team": "Chemistry", "score": 78},
    {"id": 3, "name": "Carol", "team": "Biology", "score": 85},
    {"id": 4, "name": "Dan", "team": "Physics", "score": 67},
    {"id": 5, "name": "Erin", "team": "Chemistry", "score": 88},
]

# Column definitions use AG Grid's native camelCase keys.
_COLUMN_DEFS = [
    {"field": "id", "headerName": "ID", "width": 80},
    {"field": "name", "headerName": "Name", "sortable": True, "filter": True},
    {"field": "team", "headerName": "Team", "sortable": True, "filter": True},
    {"field": "score", "headerName": "Score", "sortable": True, "filter": True},
]


class AgGridPageState(rx.State):
    """State holding the selected cell ranges of the enterprise example."""

    selection: list[dict] = []

    @rx.event
    def on_cell_selection_changed(self, selected: list[dict]):
        """Store the current cell ranges emitted by the grid."""
        self.selection = selected

    @rx.var
    def selection_text(self) -> str:
        """Human-readable summary of the current cell selection."""
        if not self.selection:
            return "No cell range selected — drag over cells to select a range."
        parts = []
        for rng in self.selection:
            start = rng.get("startRow", 0)
            end = rng.get("endRow", 0)
            columns = ", ".join(rng.get("columns", []))
            parts.append(f"rows {start}–{end} on [{columns}]")
        return "Selected: " + "; ".join(parts)


def ag_grid_page() -> rx.Component:
    """Render the AG Grid component demo page."""

    # Example 1: community grid (no enterprise bundle).
    example1_component = rx.box(
        ag_grid_component(
            id="showcase_ag_grid_community",
            column_defs=_COLUMN_DEFS,
            row_data=_ROWS,
            theme="quartz",
            width="100%",
            height="100%",
        ),
        width="100%",
        height="300px",
    )

    code1 = """import reflex as rx
from gws_reflex_main.gws_components import ag_grid_component

COLUMN_DEFS = [
    {"field": "id", "headerName": "ID", "width": 80},
    {"field": "name", "headerName": "Name", "sortable": True, "filter": True},
    {"field": "team", "headerName": "Team", "sortable": True, "filter": True},
    {"field": "score", "headerName": "Score", "sortable": True, "filter": True},
]

ROWS = [
    {"id": 1, "name": "Alice", "team": "Biology", "score": 92},
    {"id": 2, "name": "Bob", "team": "Chemistry", "score": 78},
]


def my_grid() -> rx.Component:
    return rx.box(
        ag_grid_component(
            id="my_ag_grid",
            column_defs=COLUMN_DEFS,
            row_data=ROWS,
            theme="quartz",
            width="100%",
            height="100%",
        ),
        width="100%",
        height="300px",
    )
"""

    # Example 2: enterprise grid with cell range selection.
    example2_component = rx.vstack(
        rx.box(
            ag_grid_component(
                id="showcase_ag_grid_enterprise",
                column_defs=_COLUMN_DEFS,
                row_data=_ROWS,
                theme="quartz",
                enterprise=True,
                cell_selection=True,
                on_cell_selection_changed=AgGridPageState.on_cell_selection_changed,
                width="100%",
                height="100%",
            ),
            width="100%",
            height="300px",
        ),
        rx.text(AgGridPageState.selection_text, size="2", color="var(--gray-11)"),
        align="start",
        width="100%",
        spacing="2",
    )

    code2 = """import reflex as rx
from gws_reflex_main.gws_components import ag_grid_component


class MyState(rx.State):
    selection: list[dict] = []

    @rx.event
    def on_cell_selection_changed(self, selected: list[dict]):
        # Each range is {startRow, endRow, columns} (0-based row indices).
        self.selection = selected


def my_grid() -> rx.Component:
    return rx.box(
        ag_grid_component(
            id="my_ag_grid",
            column_defs=COLUMN_DEFS,
            row_data=ROWS,
            theme="quartz",
            enterprise=True,           # load the ag-grid-enterprise bundle
            cell_selection=True,       # enable cell range selection
            on_cell_selection_changed=MyState.on_cell_selection_changed,
            width="100%",
            height="100%",
        ),
        width="100%",
        height="300px",
    )
"""

    usage_note = rx.callout(
        rx.vstack(
            rx.text(
                "Column definitions and row data use AG Grid's native camelCase keys.",
                weight="bold",
            ),
            rx.text(
                "column_defs is a list of dicts (headerName, field, sortable, filter, "
                "width, ...) and row_data is a list of dicts keyed by column field. Both "
                "accept plain values or state Vars.",
                size="2",
            ),
            rx.text(
                "Community by default; enterprise on demand.",
                weight="bold",
                margin_top="0.5em",
            ),
            rx.text(
                "enterprise defaults to False (community grid). Cell range selection "
                "(cell_selection + on_cell_selection_changed) needs enterprise=True; "
                "passing those without it raises a ValueError. on_cell_selection_changed "
                "receives a list of {startRow, endRow, columns} dicts.",
                size="2",
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
        "AG Grid Component",
        "A data grid built on ag-grid-react. Community by default, with an optional "
        "enterprise bundle for cell range selection.",
        usage_note,
        # Community grid example
        example_tabs(
            example_component=example1_component,
            code=code1,
            title="ag_grid_component (community)",
            description="A sortable, filterable data grid. Pass column_defs and row_data "
            "with AG Grid's native camelCase keys.",
            func=ag_grid_component,
        ),
        # Enterprise grid example
        example_tabs(
            example_component=example2_component,
            code=code2,
            title="Cell range selection (enterprise)",
            description="Set enterprise=True and cell_selection=True to select cell ranges. "
            "on_cell_selection_changed emits {startRow, endRow, columns} dicts.",
            func=ag_grid_component,
        ),
    )
