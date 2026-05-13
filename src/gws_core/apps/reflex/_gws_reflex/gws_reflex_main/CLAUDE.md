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

### `user_with_date_component()`
Display user photo (or initials) and a date horizontally without the user name. A dense way to show both user and timestamp information in a compact layout.

### `user_select()`
User selection component for forms and filters.

---

## Group Components

### `group_inline_component()`
Display group information inline with customizable styling.

### `group_select()`
Group selection component for forms and filters.

---

## Resource Components

### `resource_select_button()`
Resource selection component with search dialog. Allows searching and selecting resources from the database with filters for name, flagged status, and archived status.

**State: `ResourceSelectState`**
Extend this state to handle resource selection:
- Implement `on_resource_selected(resource_model)` to handle selection logic
- Override `create_search_builder()` to add custom filters (e.g., filter by resource type)

---

## Rich Text Components

### `rich_text_component()`
Rich text editor component using dc-text-editor Angular component. Provides a WYSIWYG editor for formatted text content.

---

## Input Search Components

### `input_search_component()`
Input search component using dc-input-search web component. Provides a searchable input field with autocomplete functionality. Triggers search requests as the user types and displays results in a dropdown.

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
    resource_select_button,
    ResourceSelectState,
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

## Download Service

### `ReflexDownloadService`
Generic one-shot download service for serving files over HTTP instead of through the Reflex websocket event channel. Large payloads sent through the websocket freeze the UI; this service streams them from disk via a FastAPI route. It also works around `rx.download(url=...)` resolving against the frontend origin — the service builds an absolute backend URL and triggers the download via a scripted `<a>` click.

**Three-step usage:**

1. Mount the API once in your app entrypoint:
   ```python
   app = register_gws_reflex_app(rxe.App(...))
   app.api_transformer = ReflexDownloadService.build_api()
   ```
   If your app already composes its own FastAPI sub-app, use `ReflexDownloadService.register_routes(api)` to attach the download route alongside yours.

2. In a background event, write your file and register it:
   ```python
   path = ReflexDownloadService.make_temp_path(suffix=".xlsx")
   df.to_excel(path)
   token = ReflexDownloadService.register(path, "results.xlsx", XLSX_MEDIA_TYPE)
   ```

3. Yield the download event:
   ```python
   yield ReflexDownloadService.trigger_download(token, "results.xlsx")
   ```

Tokens are single-use (the first GET consumes the entry). Files are NOT auto-deleted — caller owns the lifecycle. `make_temp_path()` places files under the lab's managed tmp dir (`Settings.make_temp_dir()`), not `/tmp`, so they share the lab's storage volume and cleanup policies.

---

## Example

Example implementations can be found in the Reflex showcase applications.
