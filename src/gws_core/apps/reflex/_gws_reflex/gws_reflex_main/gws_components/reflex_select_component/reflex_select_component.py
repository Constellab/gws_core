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
    MANTINE_SELECT_CLASS,
    SELECT_CSS,
    MantineBaseComponent,
    mantine_chevron,
    mantine_input_styles,
    mantine_select_class_names,
)

# On focus, empty the searchable input's visible text so the user can type a new
# query without first erasing the current label.
_CLEAR_SEARCH_ON_FOCUS_JS = Var(
    "(e) => { const i = e.currentTarget;"
    " const set = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
    " set.call(i, ''); i.dispatchEvent(new Event('input', { bubbles: true })); }"
)


class SelectComponent(MantineBaseComponent):
    """Reflex wrapper around the Mantine single ``Select`` component.

    A drop-in single-select dropdown: ``value`` is a single option value and
    ``on_change`` is called with the newly selected value. By default a value,
    once set, cannot be cleared by clicking it again (``allow_deselect=False``),
    so ``on_change`` never receives ``None``. Set ``searchable=True`` to add a
    type-to-filter search field inside the dropdown. Only the props used by the
    GWS apps are exposed; everything else can be passed through ``props``.
    """

    tag = "Select"

    # Data used to render options: strings, ``{value, label}`` dicts, or dataclass
    # instances exposing ``value``/``label``. Typed loosely as ``list`` so a state
    # Var of typed DTOs (or a concatenation of literals + a DTO list) is accepted.
    data: Var[list]

    # Controlled component value (the selected option value, or ``None``).
    value: Var[str]

    # Input label, displayed above the input.
    label: Var[str]

    # Placeholder displayed when the input is empty.
    placeholder: Var[str]

    # Whether the options are filtered based on the search query (adds a search field).
    searchable: Var[bool]

    # Whether clicking the currently selected option deselects it (Mantine default is
    # True). Defaulted to False here so a single select always keeps a value once set.
    allow_deselect: Var[bool]

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

    # Mantine per-slot styles (e.g. ``{"input": {...}}``).
    styles: Var[dict]

    # Mantine per-slot class names (e.g. ``{"option": "..."}``).
    class_names: Var[dict]

    # Called when the value changes. Receives the newly selected value.
    on_change: rx.EventHandler[lambda value: [value]]


def select_component(
    *,
    data: Var[list[str | dict]] | list[str | dict],
    value: Var[str] | str | None = None,
    on_change: rx.EventHandler | Any | None = None,
    label: str | None = None,
    placeholder: str | None = None,
    searchable: bool = False,
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
    :param on_change: Event handler called with the newly selected value when the
        selection changes. Deselection is disabled by default (``allow_deselect``),
        so it does not receive ``None``; pass ``allow_deselect=True`` to allow it.
    :param label: Optional label displayed above the input.
    :param placeholder: Optional placeholder shown when the input is empty.
    :param searchable: Whether the options can be filtered by typing. Defaults to ``False``.
        When ``True``, focusing the input clears the visible text so the user can type
        a new query straight away; the previously selected value stays selected (and its
        label is restored on blur if nothing else is picked).
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
    # A caller can override by passing their own right_section.
    props.setdefault("right_section", mantine_chevron())

    # Keep a value once one is set: clicking the selected option must not clear it
    # (Mantine's allowDeselect defaults to True and would emit on_change(None)).
    props.setdefault("allow_deselect", False)

    # In searchable mode, clear the visible text on focus so the user can type
    # right away (see _CLEAR_SEARCH_ON_FOCUS_JS). Merged into any caller custom_attrs.
    if searchable:
        custom_attrs = props.setdefault("custom_attrs", {})
        custom_attrs.setdefault("onFocus", _CLEAR_SEARCH_ON_FOCUS_JS)

    # Match the resting outer style (radius, border, background) of the app's
    # Radix selects so this blends in. Overridable via a caller-supplied styles.
    props.setdefault("styles", mantine_input_styles(exact_height=True))
    # Tag the dropdown options so the accent-hover CSS can target them.
    props.setdefault("class_names", mantine_select_class_names())

    # Scope the rotation CSS to this component via a stable class, keeping any
    # class the caller passed.
    caller_class = props.pop("class_name", None)
    props["class_name"] = (
        f"{MANTINE_SELECT_CLASS} {caller_class}" if caller_class else MANTINE_SELECT_CLASS
    )

    return rx.fragment(
        rx.el.style(SELECT_CSS),
        SelectComponent.create(
            data=data,
            searchable=searchable,
            disabled=disabled,
            **props,
        ),
    )
