# GWS Core Streamlit Main Module

This module provides extended utilities, components, and widgets for building Streamlit applications within the GWS Core (Constellab) ecosystem. It extends the `gws_streamlit_base` module with GWS Core-specific functionality.

All public components and widgets must be exported in the `__init__.py` file of the `gws_streamlit_main` module. If you add new components or widgets, ensure they are properly documented here.

**Note:** All elements from `gws_streamlit_base` are automatically available when importing from `gws_streamlit_main`.

**Important:** Always import from `gws_streamlit_main` in your Streamlit apps.

See [gws_streamlit_base/CLAUDE.md](../gws_streamlit_base/CLAUDE.md) for full documentation of base components.

---

## State Management

### `StreamlitMainState`
Main state class for Streamlit apps (non-virtual environment) with resource management capabilities. Extends `StreamlitStateBase` with GWS Core-specific functionality.

**Key Methods:**
- `register_streamlit_app()`: Register and initialize a GWS Streamlit app
- `get_sources()`: Load resources from source IDs (cached with `@st.cache_data`)
- `get_params()`: Return app parameters
- `get_param(key, default)`: Return a specific app parameter by key with an optional default
- `get_and_check_current_user()`: Return the current connected user (cached with `@st.cache_data`)

---

## Components

### `class_doc_component()`
Display class documentation in a formatted layout extracted via ReflectorHelper. Import from `gws_streamlit_main.components`.

### `render_method_doc()`
Render method documentation from a MethodDoc object extracted via ReflectorHelper.

### `StreamlitOpenAiChat`
Display and manage OpenAI chat conversations with message history and GPT integration.

### `ResourceSearchInput`
Search and select resources with advanced filtering including type, tags, origin, and folder filters.


## GWS Components

### `rich_text_editor()`
Add a rich text editor component to your Streamlit app with customizable height and placeholder.

### `StreamlitMenuButton`
Create a dropdown menu button with hierarchical items, icons, and click handlers. Use `StreamlitMenuButtonItem` to define individual menu items.

### `StreamlitResourceSelect`
Select a GWS resource using a pretty search with advanced search but limited filtering options.

### `StreamlitTaskRunner`
Generate a form to configure and run a GWS task with automatic validation and execution.

### `StreamlitTreeMenu`
Create a tree menu with selectable hierarchical items and icon support. Use `StreamlitTreeMenuItem` to define individual tree items.

---

## Utils

### `StreamlitAuthenticateUser`
Context manager to authenticate the current user in standalone code blocks.

## Example

Example usage of the widgets and components can be found in the `../impl/apps/streamlit_showcase/_streamlit_showcase_app/pages` directory.
