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

CHEVRON_CSS = (
    f".{MANTINE_SELECT_CLASS} .{_CHEVRON_CLASS}{{transition:transform 150ms ease;}}"
    f".{MANTINE_SELECT_CLASS}:has(input[data-expanded]) .{_CHEVRON_CLASS}"
    "{transform:rotate(180deg);}"
)


def mantine_chevron() -> rx.Component:
    """The single down-chevron used as the right section (rotates when open)."""
    return rx.icon("chevron-down", size=16, color="var(--gray-9)", class_name=_CHEVRON_CLASS)
