# GWS Core Streamlit Base Module

This module provides the foundational utilities and state management for building Streamlit applications within the GWS Core (Constellab) ecosystem. These elements are available both directly from `gws_streamlit_base` and are automatically included when importing from `gws_streamlit_main`.

All public components and states must be exported in the `__init__.py` file of the `gws_streamlit_base` module. If you add new components or states, ensure they are properly documented here.

**Important:** Always import from `gws_streamlit_main` in your Streamlit apps.

---

## State Management

### `StreamlitMainStateBase`
Base state class for all Streamlit apps with core app configuration, authentication, and parameter management. This is an abstract class that should be extended by specific implementations.

**Key Methods:**
- `get_params()`: Return app parameters
- `get_param(key, default)`: Return a specific app parameter by key with an optional default
- `get_current_user_id()`: Return the current connected user ID

### `StreamlitAppConfig`
TypedDict defining the structure of app configuration including app directory path, source IDs, parameters, authentication requirements, and user access tokens.

---

## Components

### `StreamlitContainers`
Create custom styled containers including centered layouts, rows, grids, and full-height containers.

### `dataframe_paginated()`
Display a paginated dataframe with configurable row and column pagination options.

---

## Utils

### `StreamlitHelper`
Helper utilities for CSS class generation, file uploads, sidebar management, and page height calculation.

### `StreamlitRouter`
Manage multi-page routing in Streamlit apps with page registration and navigation.

### `StreamlitTranslateService`
Handle multi-language translations by loading JSON translation files and switching languages.

---

## Example

Example implementations can be found in the Streamlit showcase applications at `../impl/apps/streamlit_showcase/_streamlit_showcase_app/pages`.
