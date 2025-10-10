# GWS Core Streamlit Module

This module provides utilities, components, and widgets for building Streamlit applications within the GWS Core (Constellab) ecosystem.

---

## Components

### `rich_text_editor()`
Add a rich text editor component to your Streamlit app with customizable height and placeholder.

### `StreamlitMenuButton`
Create a dropdown menu button with hierarchical items, icons, and click handlers.

### `StreamlitMenuButtonItem`
Define an item in a menu button with label, icon, children, and click handler.

### `StreamlitTreeMenu`
Create a tree menu with selectable hierarchical items and icon support.

### `StreamlitTreeMenuItem`
Define an item in a tree menu with label, icon, and optional children.

### `StreamlitResourceSelect`
Select a GWS resource using a search component with tag and filter support.

### `StreamlitTaskRunner`
Generate a form to configure and run a GWS task with automatic validation and execution.

---

## Widgets

### `StreamlitState`
Manage Streamlit app state including current user, authentication info, and app configuration.

### `StreamlitAuthenticateUser`
Context manager to authenticate the current user in standalone code blocks.

### `StreamlitContainers`
Create custom styled containers including centered layouts, rows, grids, and full-height containers.

### `StreamlitGridCell`
Define a cell in a grid container with column span, row span, and custom CSS style.

### `dataframe_paginated()`
Display a paginated dataframe with configurable row and column pagination options.

### `StreamlitHelper`
Helper utilities for CSS class generation, file uploads, sidebar management, and page height calculation.

### `StreamlitTranslateService`
Handle multi-language translations by loading JSON translation files and switching languages.

### `StreamlitTranslateLang`
Enum defining supported languages (FR, EN) for translation service.

### `StreamlitOpenAiChat`
Display and manage OpenAI chat conversations with message history and GPT integration.

### `ResourceSearchInput`
Search and select resources with advanced filtering including type, tags, origin, and folder filters.

### `StreamlitRouter`
Manage multi-page routing in Streamlit apps with page registration and navigation.

---

## Usage

Import components and widgets from the streamlit module `gws_core.streamlit`

## Example

Example usage of the widgets and components can be found in the `../impl/apps/streamlit_showcase/_streamlit_showcase_app/pages` directory.
