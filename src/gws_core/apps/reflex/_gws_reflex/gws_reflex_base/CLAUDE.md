# GWS Core Reflex Base Module

This module provides the foundational utilities, base components, and state management for building Reflex applications within the GWS Core (Constellab) ecosystem. These elements are available both directly from `gws_reflex_base` and are automatically included when importing from `gws_reflex_main`.

All public components and states must be exported in the `__init__.py` file of the `gws_reflex_base` module. If you add new components or states, ensure they are properly documented here.

---

## State Management

### `ReflexMainStateBase`
Base state for all Reflex apps with core app configuration, authentication, and parameter management. Provides methods to:
- Access app configuration and parameters
- Manage authentication and user access tokens
- Handle query parameters
- Check if running in dev mode or virtual environment
- Access child states with `get_first_child_of_state()`

This is the foundation for both `ReflexMainState` (in gws_reflex_main) and `ReflexMainStateEnv` (in gws_reflex_base).

### `ReflexMainStateEnv`
Main state for Reflex virtual environment apps where gws_core is not fully loaded. Extends `ReflexMainStateBase` with:
- `get_source_paths()`: Returns the paths of input resources

### `ReflexConfigDTO`
TypedDict defining the structure of app configuration including app directory path, source IDs, parameters, authentication requirements, and user access tokens.

---

## Components

### `form_dialog_component()`
Reusable form dialog for create/update operations with customizable title, description, and form content. Supports both create and update modes with loading states.

**Parameters:**
- `state`: The FormDialogState subclass managing the dialog
- `title`: Dialog title (string or rx.Component for dynamic content)
- `description`: Dialog description (string or rx.Component)
- `form_content`: The form content component containing form fields
- `max_width`: Maximum width of the dialog (default: "500px")

### `FormDialogState`
Mixin state for managing form dialogs with create/update modes, loading states, and form submission handling. Must implement:
- `_clear_form_state()`: Reset form fields
- `_create(form_data)`: Handle creation logic
- `_update(form_data)`: Handle update logic

### `confirm_dialog2()`
Create a confirmation dialog component with title, content, and action buttons. This is the updated version that works with `ConfirmDialogState2`.

### `ConfirmDialogState2`
State for managing confirmation dialogs with async action support. Provides:
- `open_dialog(title, content, action)`: Open dialog with custom action
- `close_dialog()`: Close the dialog
- `confirm_action()`: Execute the confirmation action with loading state

The action must be an async generator function (use `yield` for events).

### `ConfirmDialogAction`
Type alias for confirmation dialog action: `Callable[[], AsyncGenerator]`

---

## Utilities

### `main_component()`
Wrapper component that waits for the app to be initialized before showing content. Displays a loading spinner until initialization is complete. Automatically includes the `confirm_dialog2()` component.

**Usage:**
```python
def index() -> rx.Component:
    return main_component(
        # Your app content here
        rx.heading("Welcome"),
        rx.text("App is ready!")
    )
```

### `add_unauthorized_page()`
Adds an unauthorized page to the app for handling authentication failures. Should be called when setting up your app.

**Usage:**
```python
app = rx.App()
add_unauthorized_page(app)
```

### `get_theme()`
Returns the Reflex theme configuration with teal accent color and appearance based on `GWS_THEME` environment variable.

### `ReflexUtils`
Utility class providing helper methods:
- `multiline_ellipsis_css(lines, max_width)`: Generate CSS styles for multiline text ellipsis

---

## Types

### `ReflexDialogCloseEvent`
Generic callable type for dialog close events: `Callable[[T], Awaitable[None]]`

---

## Usage

These base components are automatically available when importing from `gws_reflex_main`:

```python
from gws_reflex_main import ReflexMainState, form_dialog_component, FormDialogState
```

Or import directly from `gws_reflex_base` for virtual environment apps:

```python
from gws_reflex_base import ReflexMainStateEnv, form_dialog_component, FormDialogState
```

---

## Example

Example implementations can be found in the Reflex showcase applications.
