# GWS Core Reflex Main Module

This module provides extended utilities, components, and state management for building Reflex applications within the GWS Core (Constellab) ecosystem. It extends the `gws_reflex_base` module with GWS Core-specific functionality.

All public components and states must be exported in the `__init__.py` file of the `gws_reflex_main` module. If you add new components or states, ensure they are properly documented here.

**Note:** All elements from `gws_reflex_base` are automatically available when importing from `gws_reflex_main`, including:
- `ReflexMainStateBase`, `ReflexConfigDTO`
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

Like `select_resource_2_component()`, it calls the data lab API from the front using the authenticated user's token. On a PUBLIC app (no authenticated user) the requests are unauthenticated unless `fallback_to_system_user=True` is passed, which runs them as the system user (binds the `get_reflex_user_auth_info_with_system_fallback` state var instead of `get_reflex_user_auth_info`). **WARNING:** `fallback_to_system_user` lets any visitor of the app read and write data lab objects through the API as the system user, including uploading the editor's images.

**Images:** pass an `image_config` (`RichTextImageConfig`) to enable the image tool (it is disabled when the config is missing). It identifies the object owning the rich text, and the editor then uploads/loads the images through the lab `rich-text/{object_type}/{object_id}/image` routes. The images are stored by `RichTextFileService` in a directory dedicated to the object, so **the owner of the object must delete that directory when the object is deleted**, otherwise the images are leaked:

```python
from gws_reflex_main.gws_components import RichTextImageConfig, rich_text_component

# in the component
rich_text_component(
    value=MyState.note_content,
    output_event=MyState.handle_content_change,
    image_config=RichTextImageConfig(
        object_type=PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE,  # ex: "project_document"
        object_id=MyState.note_id,
    ),
)

# in the service deleting the object, AFTER the db transaction is committed
RichTextFileService.delete_object_dir(PROJECT_DOCUMENT_RICH_TEXT_OBJECT_TYPE, document_id)
```

`object_type` is a free-form string (`RichTextObjectType` members are accepted too, the enum inherits `str`), so a brick declares its own value as a constant. It must only contain letters, digits, `_` and `-` (it is a directory name, validated by `RichTextFileService`).

The upload is authenticated with the app token (the Angular `HttpClient` interceptor adds the app headers). The image `GET` route is **public**: an `<img>` tag cannot send those headers, so anyone with an image URL can read it. The filenames are unguessable (uuid + timestamp), but do not use the image tool for sensitive images.

---

## Input Search Components

### `input_search_component()`
Input search component using dc-input-search web component. Provides a searchable input field with autocomplete functionality. Triggers search requests as the user types and displays results in a dropdown.

---

## AG Grid Components

### `ag_grid_component()`
Data grid built on the `ag-grid-react` npm package. Exposes the AG Grid options used by the apps as typed props (`column_defs`, `row_data`, `theme`, `cell_selection`, `on_cell_selection_changed`, `auto_size_strategy`, `tooltip_show_delay`, `tooltip_hide_delay`); extra props are forwarded to the underlying component. Column definitions and row data must use AG Grid's native camelCase keys (`headerName`, `headerTooltip`, `headerClass`, `width`, ...).

`on_cell_selection_changed` receives a list of `{startRow, endRow, columns}` dicts (0-based row indices, list of selected column ids).

The `enterprise` param toggles the `ag-grid-enterprise` bundle (needed for cell range selection). It defaults to `False` (community only); set `enterprise=True` to use `cell_selection` / `on_cell_selection_changed`. Passing those without `enterprise=True` raises a `ValueError`.

Import: `from gws_reflex_main.gws_components import ag_grid_component`

---

## Select Components

### `select_component()`
Single-value select dropdown built on the `@mantine/core` `Select` component. Behaves like a regular single select (`value` is a single string, `on_change` receives a single string, or `None` when cleared) but, with `searchable=True`, adds an integrated text field to filter the options as the user types.

Exposed typed props: `data`, `value`, `label`, `placeholder`, `searchable`, `clearable`, `nothing_found_message`, `disabled`, plus the `on_change` handler; extra props are forwarded to the underlying component.

`data` is a list of strings (or `{value, label}` dicts); `value` is the selected string value. Both accept state Vars. It shares the Mantine wiring (styles + color-mode-aware `MantineProvider`) with `multi_select_component`, so no extra setup is needed.

By default it shows a single chevron that points down when closed and rotates up when the dropdown is open (replacing Mantine's static double-chevron). With `clearable=True`, a clear (×) button appears next to the chevron once a value is set. Pass your own `right_section` to override the chevron.

It is themed to blend with the app's Radix inputs: the resting outer style (radius, 1px border, surface background, text color, height) mirrors `Select.Trigger`, focus shows the same accent outline as a text field, and hovered/selected options use the theme accent (`--accent-9`) instead of Mantine's gray/blue. All via theme tokens, so it tracks the brick's accent. Override the input via a Mantine `styles` mapping (e.g. `styles={"input": {...}}`).

Import: `from gws_reflex_main.gws_components import select_component`

---

## Multi-Select Components

### `multi_select_component()`
Searchable multi-select dropdown built on the `@mantine/core` `MultiSelect` component. It shares the Mantine wiring (styles import + color-mode-aware `MantineProvider`) with `select_component`, so no extra setup is needed.

Only the props used by the apps are exposed as typed props (`data`, `value`, `label`, `placeholder`, `searchable`, `clearable`, `max_values`) plus the `on_change` handler (receives the new list of selected values); extra props are forwarded to the underlying component.

`data` is a list of strings (or `{value, label}` dicts); `value` is the list of selected string values. Both accept state Vars.

Like `select_component`, it shows the single rotating chevron by default (the clear × button appears next to it when `clearable=True` and values are set); pass your own `right_section` to override.

Import: `from gws_reflex_main.gws_components import multi_select_component`

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

# Rich text and AG Grid components (require separate import)
from gws_reflex_main.gws_components import rich_text_component, ag_grid_component
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
