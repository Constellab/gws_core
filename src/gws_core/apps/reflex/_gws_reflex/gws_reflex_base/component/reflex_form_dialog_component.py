import traceback
from abc import abstractmethod
from typing import AsyncGenerator, Optional, Union

import reflex as rx


class FormDialogState(rx.State, mixin=True):
    """Mixin state for managing a form dialog with create/update modes.

    This state can be mixed into other states to provide dialog open/close functionality
    and form submission handling for both create and update operations.
    """

    is_update_mode: bool = False
    dialog_opened: bool = False
    is_loading: bool = False

    @rx.event
    async def open_dialog(self):
        """Open the dialog in create mode.

        This method should be overridden by subclasses to reset form fields
        and prepare the dialog for creating a new item.
        """
        self.dialog_opened = True

    @rx.event
    async def close_dialog(self):
        """Close the dialog.

        This method should be overridden by subclasses to clear form fields
        and reset any state when the dialog is closed.
        """
        self.dialog_opened = False
        await self._clear_form_state()

    @abstractmethod
    async def _clear_form_state(self) -> None:
        """Clear the form state fields.

        This method must be implemented by subclasses to reset all form-related
        state variables to their default values.
        """

    @abstractmethod
    async def _create(self, form_data: dict) -> AsyncGenerator:
        """Create a new item with the provided form data.

        This method must be implemented by subclasses to handle the actual
        creation logic.

        Args:
            form_data: Dictionary containing form fields

        Yields:
            Reflex events (e.g., rx.toast, rx.redirect)
        """

    @abstractmethod
    async def _update(self, form_data: dict) -> AsyncGenerator:
        """Update an existing item with the provided form data.

        This method must be implemented by subclasses to handle the actual
        update logic.

        Args:
            form_data: Dictionary containing form fields

        Yields:
            Reflex events (e.g., rx.toast, rx.redirect)
        """

    @rx.event(background=True)  # type: ignore
    async def submit_form(self, form_data: dict):
        """Submit the form data (create or update operation).

        This method must be implemented by subclasses to handle the actual
        form submission logic, which should determine whether to create
        or update based on the current state.

        Args:
            form_data: Dictionary containing form fields
        """

        async with self:
            self.is_loading = True

        try:
            if self.is_update_mode:
                async for event in self._update(form_data):
                    yield event
            else:
                async for event in self._create(form_data):
                    yield event
        except Exception as e:
            # TODO to improve, this should use the Logger but
            # gws_core package is not available here
            print(f"Error in submit_form: {e}")
            # print the exception for debugging
            traceback.print_exc()
            yield rx.toast.error(str(e))
            return
        finally:
            async with self:
                self.is_loading = False

        async with self:
            await self.close_dialog()

    @rx.var
    def is_create_mode(self) -> bool:
        """Return True if the dialog is in create mode."""
        return not self.is_update_mode


def form_dialog_component(
    state: type[FormDialogState],
    title: Union[str, rx.Component],
    form_content: rx.Component,
    description: Optional[Union[str, rx.Component]] = None,
    max_width: str = "500px",
) -> rx.Component:
    """Reusable form dialog component for create/update operations.

    This component creates a dialog with a form inside. It supports both create and
    update modes, where the title, description, and form content can be dynamic
    based on the state.

    Args:
        state: The FormDialogState subclass managing the dialog's behavior.
               Must implement submit_form() and provide dialog_opened state.
        title: Dialog title (string or rx.Component for dynamic content).
               Can use rx.cond() for different titles in create vs update mode.
        description: Dialog description (string or rx.Component for dynamic content).
                    Can use rx.cond() for different descriptions in create vs update mode.
        form_content: The form content component containing form fields and buttons.
                     Should include form fields and submit/cancel buttons.
        max_width: Maximum width of the dialog (default: "500px")

    Returns:
        rx.Component: Dialog component with form

    Example:
        ```python
        from typing import AsyncGenerator, Optional
        from gws_reflex_main import ReflexMainState

        # In your state class
        class MyFormState(FormDialogState, rx.State):
            _editing_item: Optional[ItemDTO] = None
            form_field: str = ""

            @rx.event
            async def open_update_dialog(self, item: ItemDTO):
                self._editing_item = item
                self.form_field = item.field
                self.is_editing_item = True
                await self.open_dialog()

            async def _clear_form_state(self) -> None:
                self._editing_item = None
                self.form_field = ""
                self.is_editing_item = False

            async def _create(self, form_data: dict) -> AsyncGenerator:
                # Validate and process form_data
                field_value = form_data.get('field', '').strip()
                if not field_value:
                    yield rx.toast.error("Field is required")
                    return

                # Create the item

                # Show success and redirect
                yield rx.toast.success("Item created successfully")
                yield rx.redirect(f"/item/{created_item.id}")

            async def _update(self, form_data: dict) -> AsyncGenerator:

                # Validate and process form_data
                field_value = form_data.get('field', '').strip()
                if not field_value:
                    yield rx.toast.error("Field is required")
                    return

                # Update the item


                # Show success
                yield rx.toast.success("Item updated successfully")

        # In your component
        def my_form_content() -> rx.Component:
            return rx.vstack(
                rx.text("Field Name", size="2", weight="bold"),
                rx.input(
                    name="field",
                    placeholder="Enter field value",
                    default_value=MyFormState.form_field,
                    required=True,
                    width="100%"
                ),
                width="100%",
                spacing="1"
            )

        def my_dialog() -> rx.Component:
            return form_dialog_component(
                state=MyFormState,
                title=rx.cond(
                    MyFormState.is_editing_item,
                    "Update Item",
                    "Create Item"
                ),
                description=rx.cond(
                    MyFormState.is_editing_item,
                    "Update the item details below.",
                    "Fill in the details below to create a new item."
                ),
                form_content=my_form_content()
            )
        ```
    """

    # Convert title to component if it is a string
    title_component = rx.text(title) if isinstance(title, str) else title

    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(title_component),
                rx.cond(
                    description,
                    rx.dialog.description(description, size="2", margin_bottom="1rem"),
                ),
                rx.form(
                    form_content,
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            type="button",
                            variant="soft",
                            color_scheme="gray",
                            on_click=state.close_dialog,
                            disabled=state.is_loading,
                        ),
                        rx.button(
                            rx.spinner(loading=state.is_loading),
                            "Save",
                            type="submit",
                            disabled=state.is_loading,
                        ),
                        margin_top="1em",
                    ),
                    on_submit=state.submit_form,
                ),
                width="100%",
            ),
            max_width=max_width,
        ),
        open=state.dialog_opened,
    )
