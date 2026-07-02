"""Custom Mantine MultiSelect component wrapping ``@mantine/core`` directly.

This is a lightweight, self-contained wrapper around the Mantine ``MultiSelect``
React component. It exists so that GWS Reflex apps can use a searchable
multi-select dropdown with only a direct dependency on ``@mantine/core``.

It handles the two things a Mantine component needs:

* imports the ``@mantine/core`` styles, and
* wraps the whole app in a ``MantineProvider`` (via ``_get_app_wrap_components``)
  whose color scheme follows the current Reflex color mode.

Only the subset of Mantine ``MultiSelect`` props currently used by the GWS apps
is exposed as typed props (``data``, ``value``, ``label``, ``placeholder``,
``searchable``, ``clearable``, ``max_values`` and the ``on_change`` handler).
Any additional prop can still be forwarded through ``props``.
"""

from typing import Any

import reflex as rx
from reflex.components.component import Component
from reflex.vars.base import Var

# Mantine npm package. Version pinned to a known-compatible release.
_MANTINE_PKG = "@mantine/core"
_MANTINE_VERSION = "8.3.9"

# The MantineProvider wrapper JS asset (color-mode aware). Shared so it is only
# emitted once regardless of how many multi-selects are rendered.
_provider_asset_path = rx.asset("mantine_provider.js", shared=True)
_public_provider_path = "$/public/" + _provider_asset_path


class _MemoizedMantineProvider(Component):
    """App-level ``MantineProvider`` wrapper following the Reflex color mode.

    Mantine components must be rendered inside a ``MantineProvider``; this
    component is injected once at the top of the app tree (see
    ``MultiSelectComponent._get_app_wrap_components``).
    """

    library = _public_provider_path
    tag = "MemoizedMantineProvider"
    is_default = True


class MultiSelectComponent(rx.Component):
    """Reflex wrapper around the Mantine ``MultiSelect`` component.

    Imports the ``@mantine/core`` styles and ensures the app is wrapped in a
    ``MantineProvider``, then renders the multi-select. Only the props used by
    the GWS apps are exposed; everything else can be passed through ``props``.
    """

    library = f"{_MANTINE_PKG}@{_MANTINE_VERSION}"
    tag = "MultiSelect"

    # Data used to render options. An array of strings or ``{value, label}`` dicts.
    data: Var[list[str | dict]]

    # Controlled component value (list of selected option values).
    value: Var[list[str]]

    # Input label, displayed above the input.
    label: Var[str]

    # Placeholder displayed when the input is empty.
    placeholder: Var[str]

    # Whether options are filtered based on the search query.
    searchable: Var[bool]

    # Whether the value can be cleared via a clear button on the right side.
    clearable: Var[bool]

    # Maximum number of values that can be picked.
    max_values: Var[int]

    # Called when the value changes. Receives the new list of selected values.
    on_change: rx.EventHandler[lambda value: [value]]

    def add_imports(self) -> dict[str, list[str]]:
        """Import the Mantine core styles."""
        return {"": [f"{_MANTINE_PKG}/styles.css"]}

    @staticmethod
    def _get_app_wrap_components() -> dict[tuple[int, str], Component]:
        """Wrap the whole app in a ``MantineProvider`` exactly once."""
        return {
            (44, "MantineProvider"): _MemoizedMantineProvider.create(),
        }


def multi_select_component(
    *,
    data: Var[list[str | dict]] | list[str | dict],
    value: Var[list[str]] | list[str],
    on_change: rx.EventHandler | Any | None = None,
    label: str | None = None,
    placeholder: str | None = None,
    searchable: bool = False,
    clearable: bool = False,
    max_values: int | None = None,
    **props,
) -> MultiSelectComponent:
    """Create a Mantine multi-select dropdown.

    :param data: Options to render — a list of strings (or ``{value, label}``
        dicts), or a state Var resolving to one.
    :param value: Currently selected values (list of strings) or a state Var.
    :param on_change: Event handler called with the new list of selected values
        when the selection changes.
    :param label: Optional label displayed above the input.
    :param placeholder: Optional placeholder shown when the input is empty.
    :param searchable: Whether options can be filtered by typing. Defaults to ``False``.
    :param clearable: Whether a clear button is shown to reset the value.
        Defaults to ``False``.
    :param max_values: Optional maximum number of values that can be selected.
    :param props: Any additional props forwarded to the underlying Mantine
        ``MultiSelect`` component.
    :return: The configured :class:`MultiSelectComponent`.
    """
    if on_change is not None:
        props["on_change"] = on_change
    if label is not None:
        props["label"] = label
    if placeholder is not None:
        props["placeholder"] = placeholder
    if max_values is not None:
        props["max_values"] = max_values

    return MultiSelectComponent.create(
        data=data,
        value=value,
        searchable=searchable,
        clearable=clearable,
        **props,
    )
