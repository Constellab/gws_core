"""Custom Mantine MultiSelect component wrapping ``@mantine/core`` directly.

This is a lightweight, self-contained wrapper around the Mantine ``MultiSelect``
React component. It exists so that GWS Reflex apps can use a searchable
multi-select dropdown with only a direct dependency on ``@mantine/core``.

The shared Mantine wiring (styles import + color-mode-aware ``MantineProvider``)
lives in :mod:`..reflex_mantine.mantine_base`; this module only declares the
``MultiSelect`` tag and the subset of props the GWS apps use (``data``,
``value``, ``label``, ``placeholder``, ``searchable``, ``clearable``,
``max_values`` and the ``on_change`` handler). Any additional prop can still be
forwarded through ``props``.
"""

from collections.abc import Sequence
from typing import Any

import reflex as rx
from reflex.components.component import Component
from reflex.vars.base import Var

from ..reflex_mantine.mantine_base import (
    MANTINE_SELECT_CLASS,
    SELECT_CSS,
    MantineBaseComponent,
    mantine_chevron,
    mantine_input_styles,
    mantine_select_class_names,
)


class MultiSelectComponent(MantineBaseComponent):
    """Reflex wrapper around the Mantine ``MultiSelect`` component.

    Only the props used by the GWS apps are exposed; everything else can be
    passed through ``props``.
    """

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

    # Custom node rendered on the right side of the input (replaces the default chevron).
    right_section: Var[Component]

    # Mantine per-slot styles (e.g. ``{"input": {...}}``).
    styles: Var[dict]

    # Mantine per-slot class names (e.g. ``{"option": "..."}``).
    class_names: Var[dict]

    # Called when the value changes. Receives the new list of selected values.
    on_change: rx.EventHandler[lambda value: [value]]


def multi_select_component(
    *,
    data: Var[list[str | dict]] | Sequence[str | dict],
    value: Var[list[str]] | list[str],
    on_change: rx.EventHandler | Any | None = None,
    label: str | None = None,
    placeholder: str | None = None,
    searchable: bool = False,
    clearable: bool = False,
    max_values: int | None = None,
    **props,
) -> rx.Component:
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
    :return: The multi-select, wrapped in a fragment together with the scoped CSS
        that rotates its chevron when the dropdown opens.
    """
    if on_change is not None:
        props["on_change"] = on_change
    if label is not None:
        props["label"] = label
    if placeholder is not None:
        props["placeholder"] = placeholder
    if max_values is not None:
        props["max_values"] = max_values

    # Single down-chevron that rotates up when the dropdown opens, matching
    # select_component. Mantine keeps the clear (×) button next to it when
    # clearable and a value is set. Override with your own right_section.
    props.setdefault("right_section", mantine_chevron())
    props.setdefault("styles", mantine_input_styles())
    props.setdefault("class_names", mantine_select_class_names())

    caller_class = props.pop("class_name", None)
    props["class_name"] = f"{MANTINE_SELECT_CLASS} {caller_class}" if caller_class else MANTINE_SELECT_CLASS

    return rx.fragment(
        rx.el.style(SELECT_CSS),
        MultiSelectComponent.create(
            data=data,
            value=value,
            searchable=searchable,
            clearable=clearable,
            **props,
        ),
    )
