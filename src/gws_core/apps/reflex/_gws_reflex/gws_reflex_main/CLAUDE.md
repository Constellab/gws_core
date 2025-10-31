# GWS Core Reflex Main Module

This module provides extended utilities, components, and state management for building Reflex applications within the GWS Core (Constellab) ecosystem. It extends the `gws_reflex_base` module with GWS Core-specific functionality.

All public components and states must be exported in the `__init__.py` file of the `gws_reflex_main` module. If you add new components or states, ensure they are properly documented here.

**Note:** All elements from `gws_reflex_base` are automatically available when importing from `gws_reflex_main`, including:
- `ReflexMainStateBase`, `ReflexMainStateEnv`, `ReflexConfigDTO`
- `form_dialog_component()`, `FormDialogState`
- `confirm_dialog2()`, `ConfirmDialogState2`, `ConfirmDialogAction`
- `main_component()`, `add_unauthorized_page()`, `get_theme()`
- `ReflexUtils`, `ReflexDialogCloseEvent`

See [gws_reflex_base/CLAUDE.md](../gws_reflex_base/CLAUDE.md) for full documentation of base components.

---

## State Management

### `ReflexMainState`
Main state for Reflex apps (non-virtual environment) with resource management capabilities. Extends `ReflexMainStateBase` with:
- `get_resources()`: Access input resources as Resource objects
- `get_current_user()`: Get the current authenticated user (returns Optional[User])
- `get_and_check_current_user()`: Get current user and verify authentication (raises exception if not authenticated)
- `authenticate_user()`: Returns ReflexAuthUser context manager for authenticated operations

### `ReflexAuthUser`
Context manager to authenticate the current user in standalone code blocks. Sets up authentication context for app operations.

**Usage:**
```python
async def my_action(self):
    with await self.authenticate_user():
        # Authenticated code here
        service = MyService()
        service.do_something()
```

---

## User Components

### `user_inline_component()`
Display user photo (or initials) and name horizontally with customizable avatar size.

### `user_profile_picture()`
Display user profile picture or initials fallback.

### `user_select()`
User selection component for forms and filters.

---

## Group Components

### `group_inline_component()`
Display group information inline with customizable styling.

### `group_select()`
Group selection component for forms and filters.

---

## Rich Text Components

### `rich_text_component()`
Rich text editor component using dc-text-editor Angular component. Provides a WYSIWYG editor for formatted text content.

---

## Usage

Import components and state from `gws_reflex_main` module:

```python
from gws_reflex_main import (
    ReflexMainState,
    ReflexAuthUser,
    user_inline_component,
    user_select,
    group_select,
    # Base components are also available
    form_dialog_component,
    FormDialogState,
    confirm_dialog2,
    ConfirmDialogState2,
    main_component,
)

# Rich text component (requires separate import)
from gws_reflex_main.gws_components import rich_text_component
```

---

## Example

Example implementations can be found in the Reflex showcase applications.
