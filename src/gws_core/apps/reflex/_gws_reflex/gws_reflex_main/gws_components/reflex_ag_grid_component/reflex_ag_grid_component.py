"""Custom AG Grid component wrapping ``ag-grid-react`` directly.

This is a lightweight, self-contained wrapper around the ``ag-grid-react`` React
component. It exists so that GWS Reflex apps can use an AG Grid data grid
**without depending on the ``reflex-enterprise`` Python package**.

It still relies on the ``ag-grid-enterprise`` JavaScript library for the
enterprise-only *cell range selection* feature (``cell_selection`` +
``on_cell_selection_changed``). The AG Grid license key is read from the
``AG_GRID_LICENSE_KEY`` environment variable; when it is not set the grid runs
in trial mode (watermark), exactly like the ``reflex-enterprise`` wrapper did.

Only the subset of AG Grid options currently used by the GWS apps is exposed as
typed props. Column definitions and row data are passed through untouched, so
they must already use AG Grid's native camelCase keys (``headerName``,
``headerTooltip``, ``headerClass``, ``width``, ...).
"""

import os
from collections.abc import Mapping, Sequence
from typing import Any, Literal

import reflex as rx
from reflex.vars.base import Var
from reflex.vars.object import ObjectVar

# AG Grid npm packages. Versions are pinned to match what the apps already use.
_AG_GRID_VERSION = "34.3.1"
_BASE_PKG = "ag-grid-react"
_COMMUNITY_PKG = "ag-grid-community"
_ENTERPRISE_PKG = "ag-grid-enterprise"

# Environment variable holding the AG Grid enterprise license key (optional).
_AG_GRID_LICENSE_KEY_ENV = "AG_GRID_LICENSE_KEY"

# Enterprise modules required for the features used by GWS apps.
_ENTERPRISE_MODULES = ["CellSelectionModule"]

# Mapping of the ``theme`` prop to the AG Grid legacy CSS theme class names.
_THEMES: dict[str, dict[str, str]] = {
    "quartz": {"light": "ag-theme-quartz", "dark": "ag-theme-quartz-dark"},
    "balham": {"light": "ag-theme-balham", "dark": "ag-theme-balham-dark"},
    "alpine": {"light": "ag-theme-alpine", "dark": "ag-theme-alpine-dark"},
    "material": {"light": "ag-theme-material", "dark": "ag-theme-material-dark"},
}
_DEFAULT_THEME = "quartz"

AgGridTheme = Literal["quartz", "balham", "alpine", "material"]


def _on_cell_selection_change_spec(
    event: ObjectVar[dict],
) -> tuple[Var[list[dict]]]:
    """Transform the AG Grid cell selection event into the shape used by the state.

    Mirrors the ``reflex-enterprise`` behaviour: reads the current cell ranges
    from the grid API and returns a list of ``{startRow, endRow, columns}``
    dictionaries. ``startRow`` / ``endRow`` are 0-based row indices and
    ``columns`` is the list of selected column ids.
    """
    return (
        Var(
            f"""{event}.api.getCellRanges().map((range) => ({{
                startRow: range.startRow.rowIndex,
                endRow: range.endRow.rowIndex,
                columns: range.columns.map((col) => col.getColId()),
            }}))"""
        ).to(list[dict]),
    )


class AgGridComponent(rx.Component):
    """Reflex wrapper around the ``ag-grid-react`` ``AgGridReact`` component.

    Registers the required AG Grid modules and (when using enterprise features)
    the enterprise license once per app, then renders the grid. Only the props
    used by the GWS apps are exposed; everything else can be passed through
    ``grid_options`` if needed.
    """

    library = f"{_BASE_PKG}@{_AG_GRID_VERSION}"
    tag = "AgGridReact"

    # Ensure the community and enterprise packages are installed alongside the
    # react wrapper (they provide the modules and CSS themes).
    lib_dependencies: list[str] = [
        f"{_COMMUNITY_PKG}@{_AG_GRID_VERSION}",
        f"{_ENTERPRISE_PKG}@{_AG_GRID_VERSION}",
    ]

    # AG Grid expects the HTML/React ``id`` prop to be named ``gridId``.
    _rename_props: dict[str, str] = {"id": "gridId"}

    # Column definitions (native AG Grid camelCase keys).
    column_defs: Var[Sequence[Mapping[str, Any]]]

    # Row data as a list of dictionaries keyed by column field.
    row_data: Var[Sequence[Mapping[str, Any]]]

    # Enable cell range selection (enterprise feature). Can be a bool or an
    # AG Grid ``CellSelectionOptions`` dict.
    cell_selection: Var[bool | dict]

    # Auto-size strategy applied when the grid first renders its data.
    auto_size_strategy: Var[dict | None]

    # Delay in ms before a tooltip is shown / hidden.
    tooltip_show_delay: Var[int]
    tooltip_hide_delay: Var[int]

    # Fired when the set of selected cell ranges changes. Receives the list of
    # ``{startRow, endRow, columns}`` dictionaries.
    on_cell_selection_changed: rx.EventHandler[_on_cell_selection_change_spec]

    @classmethod
    def create(cls, *children, theme: AgGridTheme = _DEFAULT_THEME, **props) -> "AgGridComponent":
        """Create an AgGridComponent instance.

        :param theme: Name of the AG Grid theme to apply (``quartz`` by default).
            The matching light/dark CSS class is selected reactively from the
            current color mode.
        """
        # AG Grid needs the ``firstDataRendered`` callback to size the columns
        # once the data is available when using an auto-size strategy.
        if props.get("auto_size_strategy") is not None:
            props.setdefault(
                "on_first_data_rendered",
                rx.vars.function.ArgsFunctionOperation.create(
                    args_names=("event",),
                    return_expr=Var("event.api.sizeColumnsToFit()"),
                    _var_type=rx.EventChain,
                ),
            )

        # Resolve the theme to a color-mode-aware CSS class on the grid wrapper.
        theme_config = _THEMES.get(theme, _THEMES[_DEFAULT_THEME])
        theme_class: Var[str] = rx.color_mode_cond(theme_config["light"], theme_config["dark"])
        existing_class = props.pop("class_name", None)
        if existing_class is not None:
            # Concatenate as Vars so a reactive existing class name is preserved.
            props["class_name"] = Var.create(existing_class).to(str) + " " + theme_class
        else:
            props["class_name"] = theme_class

        return super().create(*children, **props)

    def add_imports(self) -> dict[str, list[str]]:
        """Import the module registry, the required modules, the license manager and the theme CSS."""
        return {
            "": [
                f"{_COMMUNITY_PKG}/styles/ag-grid.css",
                f"{_COMMUNITY_PKG}/styles/ag-theme-quartz.css",
                f"{_COMMUNITY_PKG}/styles/ag-theme-alpine.css",
                f"{_COMMUNITY_PKG}/styles/ag-theme-balham.css",
                f"{_COMMUNITY_PKG}/styles/ag-theme-material.css",
            ],
            _COMMUNITY_PKG: [
                "ModuleRegistry",
                "AllCommunityModule",
                "provideGlobalGridOptions",
            ],
            _ENTERPRISE_PKG: [*_ENTERPRISE_MODULES, "LicenseManager"],
        }

    def add_custom_code(self) -> list[str]:
        """Register the AG Grid modules, set the license key and opt into legacy theming."""
        license_key = os.getenv(_AG_GRID_LICENSE_KEY_ENV)
        set_license = (
            f"LicenseManager.setLicenseKey('{license_key}');"
            if license_key is not None
            else "LicenseManager.setLicenseKey(null);"
        )

        modules = ", ".join(["AllCommunityModule", *_ENTERPRISE_MODULES])

        return [
            set_license,
            f"ModuleRegistry.registerModules([{modules}]);",
            # Opt back into the v32 CSS-class based theming so the ag-theme-*
            # classes applied via ``class_name`` take effect.
            "provideGlobalGridOptions({'theme': 'legacy'});",
        ]


def ag_grid_component(
    *,
    id: str,  # noqa: A002 - matches AG Grid's / rxe.ag_grid's `id` prop name
    column_defs: Var[Sequence[Mapping[str, Any]]] | Sequence[Mapping[str, Any]],
    row_data: Var[Sequence[Mapping[str, Any]]] | Sequence[Mapping[str, Any]],
    theme: AgGridTheme = _DEFAULT_THEME,
    cell_selection: Var[bool | dict] | bool | dict | None = None,
    on_cell_selection_changed: rx.EventHandler | None = None,
    auto_size_strategy: Var[dict | None] | dict | None = None,
    tooltip_show_delay: int | None = None,
    tooltip_hide_delay: int | None = None,
    **props,
) -> AgGridComponent:
    """Create an AG Grid data grid without depending on ``reflex-enterprise``.

    This is a drop-in replacement for the subset of ``rxe.ag_grid`` used by the
    GWS apps. Column definitions and row data must use AG Grid's native
    camelCase keys.

    :param id: Unique DOM id for the grid (also used as the AG Grid ``gridId``).
    :param column_defs: AG Grid column definitions (list of dicts or a state Var).
    :param row_data: Row data as a list of dicts keyed by column field (or a state Var).
    :param theme: AG Grid theme name, defaults to ``"quartz"``.
    :param cell_selection: Enable cell range selection (enterprise). ``True`` or a
        ``CellSelectionOptions`` dict.
    :param on_cell_selection_changed: Event handler receiving the list of
        ``{startRow, endRow, columns}`` dicts when the selection changes.
    :param auto_size_strategy: AG Grid ``autoSizeStrategy`` dict, applied on first render.
    :param tooltip_show_delay: Delay in ms before tooltips appear.
    :param tooltip_hide_delay: Delay in ms before tooltips disappear.
    :param props: Any additional props forwarded to the underlying component
        (e.g. ``width``, ``height``, ``key``, ``style``).
    :return: The configured :class:`AgGridComponent`.
    """
    if cell_selection is not None:
        props["cell_selection"] = cell_selection
    if on_cell_selection_changed is not None:
        props["on_cell_selection_changed"] = on_cell_selection_changed
    if auto_size_strategy is not None:
        props["auto_size_strategy"] = auto_size_strategy
    if tooltip_show_delay is not None:
        props["tooltip_show_delay"] = tooltip_show_delay
    if tooltip_hide_delay is not None:
        props["tooltip_hide_delay"] = tooltip_hide_delay

    return AgGridComponent.create(
        id=id,
        column_defs=column_defs,
        row_data=row_data,
        theme=theme,
        **props,
    )
