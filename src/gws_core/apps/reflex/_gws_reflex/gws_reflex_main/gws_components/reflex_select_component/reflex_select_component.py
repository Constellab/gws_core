"""Custom Mantine single Select component wrapping ``@mantine/core`` directly.

This is the single-value counterpart of
:mod:`..reflex_multi_select_component.reflex_multi_select_component`. It wraps
the Mantine ``Select`` React component so GWS Reflex apps can use a dropdown
that behaves like a regular single select (``value`` is a single string,
``on_change`` receives a single string), with an optional integrated search
field enabled by ``searchable=True``.

The shared Mantine wiring (styles import + color-mode-aware ``MantineProvider``)
lives in :mod:`..reflex_mantine.mantine_base`; this module only declares the
``Select`` tag and the subset of props the GWS apps use. Any additional prop
can still be forwarded through ``props``.
"""

from typing import Any

import reflex as rx
from reflex.components.component import Component
from reflex.vars.base import Var

from ..reflex_mantine.mantine_base import (
    CHEVRON_CSS,
    MANTINE_SELECT_CLASS,
    MantineBaseComponent,
    mantine_chevron,
)


class SelectComponent(MantineBaseComponent):
    """Reflex wrapper around the Mantine single ``Select`` component.

    A drop-in single-select dropdown: ``value`` is a single option value and
    ``on_change`` is called with the newly selected value (or ``None`` when the
    value is cleared). Set ``searchable=True`` to add a type-to-filter search
    field inside the dropdown. Only the props used by the GWS apps are exposed;
    everything else can be passed through ``props``.
    """

    tag = "Select"

    # Data used to render options. An array of strings or ``{value, label}`` dicts.
    data: Var[list[str | dict]]

    # Controlled component value (the selected option value, or ``None``).
    value: Var[str]

    # Input label, displayed above the input.
    label: Var[str]

    # Placeholder displayed when the input is empty.
    placeholder: Var[str]

    # Whether the options are filtered based on the search query (adds a search field).
    searchable: Var[bool]

    # Whether the value can be cleared via a clear button on the right side.
    clearable: Var[bool]

    # Message displayed when no option matches the search query (searchable only).
    nothing_found_message: Var[str]

    # Whether the select is disabled.
    disabled: Var[bool]

    # Name of the underlying input, for native form submission.
    name: Var[str]

    # Uncontrolled default value.
    default_value: Var[str]

    # Custom node rendered on the right side of the input (replaces the default chevron).
    right_section: Var[Component]

    # Called when the value changes. Receives the newly selected value (or ``None``).
    on_change: rx.EventHandler[lambda value: [value]]


def select_component(
    *,
    data: Var[list[str | dict]] | list[str | dict],
    value: Var[str] | str | None = None,
    on_change: rx.EventHandler | Any | None = None,
    label: str | None = None,
    placeholder: str | None = None,
    searchable: bool = False,
    clearable: bool = False,
    nothing_found_message: str | None = None,
    disabled: bool = False,
    **props,
) -> rx.Component:
    """Create a Mantine single-select dropdown.

    Behaves like a regular single select but, with ``searchable=True``, adds an
    integrated text field to filter the options as the user types.

    :param data: Options to render — a list of strings (or ``{value, label}``
        dicts), or a state Var resolving to one.
    :param value: Currently selected value (a single string) or a state Var.
    :param on_change: Event handler called with the newly selected value (or
        ``None`` when cleared) when the selection changes.
    :param label: Optional label displayed above the input.
    :param placeholder: Optional placeholder shown when the input is empty.
    :param searchable: Whether the options can be filtered by typing. Defaults to ``False``.
    :param clearable: Whether a clear button is shown to reset the value.
        Defaults to ``False``.
    :param nothing_found_message: Optional message shown when no option matches
        the search query (only relevant when ``searchable=True``).
    :param disabled: Whether the select is disabled. Defaults to ``False``.
    :param props: Any additional props forwarded to the underlying Mantine
        ``Select`` component.
    :return: The select, wrapped in a fragment together with the scoped CSS that
        rotates its chevron when the dropdown opens.
    """
    if value is not None:
        props["value"] = value
    if on_change is not None:
        props["on_change"] = on_change
    if label is not None:
        props["label"] = label
    if placeholder is not None:
        props["placeholder"] = placeholder
    if nothing_found_message is not None:
        props["nothing_found_message"] = nothing_found_message

    # Replace Mantine's static double-chevron with a single chevron that points
    # down when closed and rotates up when the dropdown is open (see CHEVRON_CSS).
    # When clearable and a value is set, Mantine renders its clear (×) button next
    # to this chevron, so overriding the right section keeps the clear button.
    # A caller can override by passing their own right_section.
    props.setdefault("right_section", mantine_chevron())

    # Scope the rotation CSS to this component via a stable class, keeping any
    # class the caller passed.
    caller_class = props.pop("class_name", None)
    props["class_name"] = f"{MANTINE_SELECT_CLASS} {caller_class}" if caller_class else MANTINE_SELECT_CLASS

    return rx.fragment(
        rx.el.style(CHEVRON_CSS),
        SelectComponent.create(
            data=data,
            searchable=searchable,
            clearable=clearable,
            disabled=disabled,
            **props,
        ),
    )
