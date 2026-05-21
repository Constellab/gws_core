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

This is the foundation for both `ReflexMainState` (in gws_reflex_main) and `ReflexMainStateEnv` (in gws_reflex_env_main).

### `ReflexConfigDTO`
TypedDict defining the structure of app configuration including app directory path, source IDs, parameters, authentication requirements, and user access tokens.

---

## Components

- **reflex_form_dialog_component.py**
  - `form_dialog_component()`: Reusable form dialog for create/update operations with customizable title, description, and form content
  - `FormDialogState`: Mixin state for managing form dialogs with create/update modes, loading states, and form submission handling
- **reflex_confirm_dialog_component.py**
  - `confirm_dialog()`: Confirmation dialog component with title, content, and action buttons
  - `ConfirmDialogState`: State for managing confirmation dialogs with async action support
  - `ConfirmDialogAction`: Type alias for confirmation dialog action: `Callable[[], AsyncGenerator]`
- **reflex_dialog_components.py**
  - `dialog_header()`: Styled header component for dialogs with title and close button
- **reflex_loader_section_component.py**
  - `loader_section()`: Loader section wrapper that displays a spinner when loading
- **reflex_page_sidebar.py**
  - `page_sidebar_component()`: Generic page layout with responsive sidebar and main content area
- **reflex_sidebar_menu_component.py**
  - `sidebar_menu_component()`: Sidebar menu with logo, title, and navigation links (use with `page_sidebar_component`)
  - `menu_item_component()`: Individual menu item with icon and label for sidebar navigation

---

## Utilities

- **reflex_utils.py**
  - `ReflexTheme`: Enum defining theme color constants (`ACCENT`, `SECONDARY`, `TERTIARY`)
  - `ReflexUtils`: Static utility class
    - `multiline_ellipsis_css(lines, max_width="100%")`: Returns CSS styles dict for multiline text ellipsis truncation
- **reflex_main_utils.py**
  - `default_gws_env_frontend_handler(exception)`: Frontend exception handler for virtual environment apps (logs with the standard library, not the GWS Logger)
  - `default_gws_env_backend_handler(exception)`: Backend exception handler for virtual environment apps (shows a toast for `ReflexAppException`, a generic message otherwise)

---

## Exceptions

- **reflex_exception.py**
  - `ReflexAppException`: Expected exception raised by a Reflex app. This is the **gws_core-free** counterpart of gws_core's `BadRequestException` — `gws_reflex_base` must not import `gws_core` since it is loaded by virtual environment apps where `gws_core` is not installed. The backend exception handler catches it to show a clean toast. Constructor: `ReflexAppException(detail, show_as="error")` where `show_as` is `"error"` or `"info"`.
  - `ReflexExceptionShowMode`: `Literal["error", "info"]` type for the `show_as` argument.

---


## Usage

These base components are automatically available when importing from `gws_reflex_main`:

```python
from gws_reflex_main import ReflexMainState, form_dialog_component, FormDialogState
```

Or import from `gws_reflex_env_main` for virtual environment apps (it re-exports everything from `gws_reflex_base`):

```python
from gws_reflex_env_main import ReflexMainStateEnv, register_gws_reflex_env_app
from gws_reflex_base import form_dialog_component, FormDialogState
```

---

## Example

Example implementations can be found in the Reflex showcase applications.
