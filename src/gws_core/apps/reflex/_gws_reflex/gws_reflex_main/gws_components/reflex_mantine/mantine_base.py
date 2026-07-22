"""Shared Mantine wiring for GWS Reflex components.

Mantine React components must be rendered inside a ``MantineProvider`` and need
the ``@mantine/core`` styles imported. This module centralises both so the
individual Mantine wrappers (single ``Select``, ``MultiSelect``, ...) only have
to declare their own ``tag`` and typed props.
"""

import reflex as rx
from reflex.components.component import Component

# Mantine npm package. Version pinned to a known-compatible release.
MANTINE_PKG = "@mantine/core"
MANTINE_VERSION = "8.3.9"

# The MantineProvider wrapper JS asset (color-mode aware). Shared so it is only
# emitted once regardless of how many Mantine components are rendered.
_provider_asset_path = rx.asset("mantine_provider.js", shared=True)
_public_provider_path = "$/public/" + _provider_asset_path


class _MemoizedMantineProvider(Component):
    """App-level ``MantineProvider`` wrapper following the Reflex color mode.

    Mantine components must be rendered inside a ``MantineProvider``; this
    component is injected once at the top of the app tree (see
    ``MantineBaseComponent._get_app_wrap_components``).
    """

    library = _public_provider_path
    tag = "MemoizedMantineProvider"
    is_default = True


class MantineBaseComponent(rx.Component):
    """Base class for ``@mantine/core`` component wrappers.

    Imports the Mantine styles and ensures the app is wrapped in a single
    color-mode-aware ``MantineProvider``. Subclasses only set their ``tag`` and
    expose the props they need.
    """

    library = f"{MANTINE_PKG}@{MANTINE_VERSION}"

    def add_imports(self) -> dict[str, list[str]]:
        """Import the Mantine core styles."""
        return {"": [f"{MANTINE_PKG}/styles.css"]}

    @staticmethod
    def _get_app_wrap_components() -> dict[tuple[int, str], Component]:
        """Wrap the whole app in a ``MantineProvider`` exactly once."""
        return {
            (44, "MantineProvider"): _MemoizedMantineProvider.create(),
        }


# --- Shared single-chevron right section --------------------------------------
# Mantine's default right section is a static double-chevron (up+down). The GWS
# Select / MultiSelect replace it with a single chevron that points down when the
# dropdown is closed and rotates up when it is open. Mantine sets ``data-expanded``
# on the input while open; when ``clearable`` and a value is set, it renders the
# clear (×) button next to this chevron, so overriding the right section keeps it.

# Class on the component root, used to scope the rotation CSS.
MANTINE_SELECT_CLASS = "gws-mantine-select"
# Class on the chevron itself, so only it rotates (not the clear button).
_CHEVRON_CLASS = "gws-mantine-chevron"
# Class on each dropdown option. The dropdown is portalled outside the component
# root, so this global class (not the root class) is what the option CSS targets.
_OPTION_CLASS = "gws-mantine-option"
# Class on the input slot (the bordered box). For the single select this is the
# ``<input>`` itself; for the multi-select it is the pills container wrapping the
# chips and the typing field. Focus styling targets it via ``:focus-within`` so the
# whole box (chips included) gets the outline, not just the inner field.
_FIELD_CLASS = "gws-mantine-field"
# Class on the portalled dropdown. Radix dialogs set ``pointer-events: none`` on
# <body> while a modal is open; the dropdown is portalled to <body>, so without
# this it becomes non-interactive inside a dialog (no hover, clicks ignored).
_DROPDOWN_CLASS = "gws-mantine-dropdown"

SELECT_CSS = (
    # Single chevron: rotate it up when the dropdown is open.
    f".{MANTINE_SELECT_CLASS} .{_CHEVRON_CLASS}{{transition:transform 150ms ease;}}"
    f".{MANTINE_SELECT_CLASS}:has(input[data-expanded]) .{_CHEVRON_CLASS}"
    "{transform:rotate(180deg);}"
    # Hovered / keyboard-active option uses the theme accent instead of Mantine's
    # gray hover and blue selected. Higher specificity than Mantine's own rules.
    # The dropdown is portalled to <body>, outside the `.radix-themes` element that
    # defines --accent-contrast, so that token is unavailable here; fall back to
    # --accent-1 (defined on :root) for readable light text on the dark accent.
    f".{_OPTION_CLASS}[data-combobox-selected],"
    f".{_OPTION_CLASS}:hover:not([data-combobox-disabled])"
    "{background-color:var(--accent-9);color:var(--accent-contrast,var(--accent-1));}"
    # Focus outline matching the app's Radix text field / input search. Targets the
    # bordered input slot via :focus-within, so on the multi-select the whole box
    # (chips + field) is outlined, not just the inner typing field.
    f".{_FIELD_CLASS}:focus-within"
    "{outline:2px solid var(--focus-8);outline-offset:-1px;}"
    # Keep the portalled dropdown interactive inside a modal Radix dialog, which
    # otherwise sets pointer-events:none on <body> (and thus on the dropdown).
    f".{_DROPDOWN_CLASS}{{pointer-events:auto;}}"
)


def mantine_chevron() -> rx.Component:
    """The single down-chevron used as the right section (rotates when open)."""
    return rx.icon("chevron-down", size=16, color="var(--gray-9)", class_name=_CHEVRON_CLASS)


def mantine_select_class_names() -> dict:
    """Mantine ``classNames`` tagging the option (accent CSS), the input slot
    (focus-outline CSS) and the dropdown (pointer-events fix inside dialogs)."""
    return {"option": _OPTION_CLASS, "input": _FIELD_CLASS, "dropdown": _DROPDOWN_CLASS}


# --- Resting outer style matching the app's Radix ``Select.Trigger`` -----------
# Mirrors the Radix surface trigger (size 2) so the Mantine input blends with the
# other selects on a page: same radius, 1px inset border, surface background and
# text color. Referenced tokens are defined by the app's Radix theme, so this
# tracks the theme automatically. Applied to the Mantine ``input`` slot, which
# works for both the single Select and the MultiSelect.
_INPUT_STYLE = {
    "borderRadius": "var(--radius-2)",
    "border": "none",
    "boxShadow": "inset 0 0 0 1px var(--gray-a7)",
    "backgroundColor": "var(--color-surface)",
    "color": "var(--gray-12)",
    "minHeight": "var(--space-6)",
    "fontSize": "var(--font-size-2)",
}


def mantine_input_styles(exact_height: bool = False) -> dict:
    """Mantine ``styles`` mapping that styles the input slot like a Radix trigger.

    :param exact_height: when True, pin the height to ``var(--space-6)`` (the Radix
        size-2 field height) so a single select lines up exactly with text inputs.
        Left off for the multi-select, whose height must grow with the pills.
    """
    style = dict(_INPUT_STYLE)
    if exact_height:
        style["height"] = "var(--space-6)"
    return {"input": style}
