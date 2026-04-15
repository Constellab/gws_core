"""Reusable paginated table component for Reflex apps.

Provides :func:`pagination_controls` for prev/next/page-size UI bound to a
:class:`PaginatedTableState` subclass, and :func:`paginated_table_component`
which wraps a caller-provided grid component together with those controls.
"""

import reflex as rx

from .paginated_table_state import PAGE_SIZE_OPTIONS, PaginatedTableState


def pagination_controls(state_cls: type[PaginatedTableState]) -> rx.Component:
    """Prev/next buttons, page size selector, and page info text."""
    return rx.hstack(
        rx.text(state_cls.page_info, size="1", color="var(--gray-a10)"),
        rx.spacer(),
        rx.hstack(
            rx.text("Rows per page", size="1", color="var(--gray-a10)"),
            rx.select(
                [str(n) for n in PAGE_SIZE_OPTIONS],
                value=state_cls.page_size.to_string(),
                on_change=state_cls.set_page_size,
                size="1",
            ),
            spacing="2",
            align="center",
        ),
        rx.hstack(
            rx.button(
                rx.icon("chevrons-left", size=14),
                on_click=state_cls.first_page,
                disabled=~state_cls.has_prev,
                variant="soft",
                size="1",
            ),
            rx.button(
                rx.icon("chevron-left", size=14),
                on_click=state_cls.prev_page,
                disabled=~state_cls.has_prev,
                variant="soft",
                size="1",
            ),
            rx.button(
                rx.icon("chevron-right", size=14),
                on_click=state_cls.next_page,
                disabled=~state_cls.has_next,
                variant="soft",
                size="1",
            ),
            rx.button(
                rx.icon("chevrons-right", size=14),
                on_click=state_cls.last_page,
                disabled=~state_cls.has_next,
                variant="soft",
                size="1",
            ),
            spacing="1",
            align="center",
        ),
        align="center",
        width="100%",
        padding="8px 12px",
        spacing="3",
        flex_shrink="0",
    )


def paginated_table_component(
    grid: rx.Component,
    state_cls: type[PaginatedTableState],
) -> rx.Component:
    """Wrap a grid component with pagination controls bound to ``state_cls``.

    The caller builds the grid (typically an AG Grid) using vars from
    ``state_cls`` (e.g. ``state_cls.ag_grid_column_defs`` and
    ``state_cls.ag_grid_row_data``) and passes it in. This wrapper stacks the
    grid on top of the pagination controls.

    Args:
        grid: The grid component to render (caller-built).
        state_cls: The ``PaginatedTableState`` subclass driving the table.
    """
    return rx.vstack(
        grid,
        pagination_controls(state_cls),
        width="100%",
        height="100%",
        spacing="0",
    )
