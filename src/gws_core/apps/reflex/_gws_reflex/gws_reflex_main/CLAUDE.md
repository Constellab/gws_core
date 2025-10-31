# GWS Core Reflex Module

This module provides utilities, components, and state management for building Reflex applications within the GWS Core (Constellab) ecosystem.

---

## State Management

### `ReflexMainState`
Main state for Reflex apps with resource management capabilities. Provides methods to access input resources and current user information.

### `ReflexAuthUser`
Context manager to authenticate the current user in standalone code blocks. Sets up authentication context for app operations.

---

## Components

### `confirm_dialog()`
Create a confirmation dialog with title, content, and action buttons. Requires `ConfirmDialogState` mixin.

### `ConfirmDialogState`
Mixin state for managing confirmation dialogs with open/close functionality and confirm action.

### `form_dialog_component()`
Reusable form dialog for create/update operations with customizable title, description, and form content.

### `FormDialogState`
Mixin state for managing form dialogs with create/update modes, loading states, and form submission handling.

### `user_inline_component()`
Display user photo (or initials) and name horizontally with customizable avatar size.

---

## Usage

Import components and state from `gws_reflex_main` module.

## Example

Example implementations can be found in the Reflex showcase applications.
