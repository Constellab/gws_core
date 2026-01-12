"""Dialog components demo page for the Reflex showcase app."""

from typing import cast

import reflex as rx
from gws_reflex_base import (
    ConfirmDialogState,
    FormDialogState,
    dialog_header,
    form_dialog_component,
)
from gws_reflex_base.component.reflex_confirm_dialog_component import confirm_dialog
from gws_reflex_main import ReflexMainState

from ..components import example_tabs, page_layout


class DialogPageState(ReflexMainState):
    """State for the dialog page."""

    # Basic dialog state
    basic_dialog_opened: bool = False
    dialog_result: str = ""

    @rx.event
    def open_basic_dialog(self):
        """Open the basic dialog."""
        self.basic_dialog_opened = True
        self.dialog_result = ""

    @rx.event
    def close_basic_dialog(self):
        """Close the basic dialog."""
        self.basic_dialog_opened = False

    @rx.event
    def handle_basic_dialog_action(self):
        """Handle basic dialog action."""
        self.dialog_result = "Dialog action performed!"
        self.basic_dialog_opened = False

    # Confirm dialog methods
    @rx.event
    async def open_confirm_dialog(self):
        """Open the confirmation dialog."""
        confirm_dialog_state = await self.get_state(ConfirmDialogState)

        confirm_dialog_state.open_dialog(
            title="Delete Item",
            content="Are you sure you want to delete this item? This action cannot be undone.",
            action=self.delete_action,
        )

    async def delete_action(self):
        """Action to perform when user confirms."""
        # Simulate a delete action
        async with self:
            self.dialog_result = "Item deleted successfully!"
        yield rx.toast.success("Item deleted successfully!")


class ExampleFormDialogState(FormDialogState, rx.State):
    """State for the form dialog example."""

    form_name: str = ""
    form_email: str = ""
    form_message: str = ""
    result_message: str = ""

    @rx.event
    async def open_create_dialog(self):
        """Open the dialog in create mode."""
        self.is_update_mode = False
        await self.open_dialog()

    @rx.event
    async def open_update_dialog(self):
        """Open the dialog in update mode with pre-filled data."""
        self.is_update_mode = True
        self.form_name = "John Doe"
        self.form_email = "john.doe@example.com"
        self.form_message = "This is a pre-filled message for update mode."
        await self.open_dialog()

    async def _clear_form_state(self) -> None:
        """Clear the form state fields."""
        self.form_name = ""
        self.form_email = ""
        self.form_message = ""
        self.is_update_mode = False

    async def _create(self, form_data: dict):
        """Create a new item with the provided form data."""
        # Validate form data
        name = form_data.get("name", "").strip()
        email = form_data.get("email", "").strip()
        message = form_data.get("message", "").strip()

        if not name:
            yield rx.toast.error("Name is required")
            return

        if not email:
            yield rx.toast.error("Email is required")
            return

        # Simulate creation
        async with self:
            self.result_message = f"Created: {name} ({email})"

        yield rx.toast.success(f"Successfully created entry for {name}")

    async def _update(self, form_data: dict):
        """Update an existing item with the provided form data."""
        # Validate form data
        name = form_data.get("name", "").strip()
        email = form_data.get("email", "").strip()

        if not name:
            yield rx.toast.error("Name is required")
            return

        if not email:
            yield rx.toast.error("Email is required")
            return

        # Simulate update
        async with self:
            self.result_message = f"Updated: {name} ({email})"

        yield rx.toast.success(f"Successfully updated entry for {name}")


def dialog_page() -> rx.Component:
    """Render the dialog components demo page."""

    # Example 1: Basic Dialog with dialog_header
    basic_dialog_component = rx.vstack(
        rx.button(
            "Open Basic Dialog",
            on_click=DialogPageState.open_basic_dialog,
        ),
        rx.cond(
            DialogPageState.dialog_result != "",
            rx.text(
                DialogPageState.dialog_result,
                color="green",
                margin_top="1em",
            ),
        ),
        # Basic dialog
        rx.dialog.root(
            rx.dialog.content(
                rx.vstack(
                    dialog_header(
                        title="Basic Dialog Example",
                        close=DialogPageState.close_basic_dialog,
                    ),
                    rx.text(
                        "This is a basic dialog using the dialog_header component. "
                        "It provides a consistent header with title and close button.",
                        margin_bottom="1em",
                    ),
                    rx.hstack(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            on_click=DialogPageState.close_basic_dialog,
                        ),
                        rx.button(
                            "Perform Action",
                            on_click=DialogPageState.handle_basic_dialog_action,
                        ),
                        spacing="3",
                    ),
                    width="100%",
                ),
                max_width="500px",
            ),
            open=DialogPageState.basic_dialog_opened,
        ),
        align="start",
    )

    code1 = """from gws_reflex_base import dialog_header
from gws_reflex_main import ReflexMainState
import reflex as rx

class MyState(ReflexMainState):
    dialog_opened: bool = False

    @rx.event
    def open_dialog(self):
        self.dialog_opened = True

    @rx.event
    def close_dialog(self):
        self.dialog_opened = False

    @rx.event
    def handle_action(self):
        # Perform your action here
        self.dialog_opened = False

# Create dialog
rx.dialog.root(
    rx.dialog.content(
        rx.vstack(
            dialog_header(
                title="My Dialog",
                close=MyState.close_dialog,
            ),
            rx.text("Dialog content goes here..."),
            rx.button(
                "Action",
                on_click=MyState.handle_action,
            ),
            width="100%",
        ),
        max_width="500px",
    ),
    open=MyState.dialog_opened,
)"""

    # Example 2: Confirm Dialog
    confirm_dialog_component = rx.vstack(
        rx.button(
            "Open Confirm Dialog",
            on_click=DialogPageState.open_confirm_dialog,
            color_scheme="red",
        ),
        rx.cond(
            DialogPageState.dialog_result != "",
            rx.text(
                DialogPageState.dialog_result,
                color="green",
                margin_top="1em",
            ),
        ),
        # The confirm dialog is globally available
        confirm_dialog(),
        align="start",
    )

    code2 = '''from gws_reflex_base import ConfirmDialogState, confirm_dialog
from gws_reflex_main import ReflexMainState
import reflex as rx

class MyState(ReflexMainState):

    @rx.event
    async def open_delete_confirmation(self, item_id: str):
        """Open the delete confirmation dialog."""
        confirm_dialog_state = await self.get_state(ConfirmDialogState)

        async def delete_action():
            """Action to perform when user confirms."""
            # Perform delete operation
            # await delete_item(item_id)

            yield rx.toast.success("Item deleted successfully!")
            # Optionally redirect or refresh data
            # yield rx.redirect("/items")

        confirm_dialog_state.open_dialog(
            title="Delete Item",
            content="Are you sure you want to delete this item? This action cannot be undone.",
            action=delete_action,
        )

# In your component
def my_component():
    return rx.fragment(
        rx.button(
            "Delete",
            on_click=lambda: MyState.open_delete_confirmation("item_123"),
            color_scheme="red",
        ),
        # Add confirm dialog to your page
        confirm_dialog(),
    )'''

    # Example 3: Form Dialog
    def form_content() -> rx.Component:
        """Create the form content for the dialog."""
        return rx.vstack(
            # Name field
            rx.vstack(
                rx.text("Name", size="2", weight="bold"),
                rx.input(
                    name="name",
                    placeholder="Enter your name",
                    default_value=ExampleFormDialogState.form_name,
                    required=True,
                    width="100%",
                ),
                width="100%",
                spacing="1",
            ),
            # Email field
            rx.vstack(
                rx.text("Email", size="2", weight="bold"),
                rx.input(
                    name="email",
                    type="email",
                    placeholder="Enter your email",
                    default_value=ExampleFormDialogState.form_email,
                    required=True,
                    width="100%",
                ),
                width="100%",
                spacing="1",
            ),
            # Message field
            rx.vstack(
                rx.text("Message", size="2", weight="bold"),
                rx.text_area(
                    name="message",
                    placeholder="Enter your message",
                    default_value=ExampleFormDialogState.form_message,
                    width="100%",
                    rows="4",
                ),
                width="100%",
                spacing="1",
            ),
            width="100%",
            spacing="4",
        )

    example3_component = rx.vstack(
        rx.hstack(
            rx.button(
                "Open Create Form",
                on_click=ExampleFormDialogState.open_create_dialog,
            ),
            rx.button(
                "Open Update Form",
                on_click=ExampleFormDialogState.open_update_dialog,
                variant="soft",
            ),
            spacing="3",
        ),
        rx.cond(
            ExampleFormDialogState.result_message != "",
            rx.text(
                ExampleFormDialogState.result_message,
                color="green",
                margin_top="1em",
            ),
        ),
        # Form dialog
        form_dialog_component(
            state=ExampleFormDialogState,
            title=cast(
                str,
                rx.cond(
                    ExampleFormDialogState.is_update_mode,
                    "Update Entry",
                    "Create New Entry",
                ),
            ),
            description=cast(
                str,
                rx.cond(
                    ExampleFormDialogState.is_update_mode,
                    "Update the entry details below.",
                    "Fill in the details below to create a new entry.",
                ),
            ),
            form_content=form_content(),
            max_width="500px",
        ),
        align="start",
    )

    code3 = '''from gws_reflex_base import FormDialogState, form_dialog_component
import reflex as rx

class MyFormState(FormDialogState, rx.State):
    form_field: str = ""

    @rx.event
    async def open_create_dialog(self):
        """Open dialog in create mode."""
        self.is_update_mode = False
        await self.open_dialog()

    @rx.event
    async def open_update_dialog(self, item_id: str):
        """Open dialog in update mode."""
        # Load existing data
        # item = load_item(item_id)
        self.form_field = "existing value"
        self.is_update_mode = True
        await self.open_dialog()

    async def _clear_form_state(self) -> None:
        """Clear form fields."""
        self.form_field = ""
        self.is_update_mode = False

    async def _create(self, form_data: dict):
        """Create new item."""
        field_value = form_data.get('field', '').strip()
        if not field_value:
            yield rx.toast.error("Field is required")
            return

        # Create item
        # await create_item(field_value)

        yield rx.toast.success("Item created successfully")

    async def _update(self, form_data: dict):
        """Update existing item."""
        field_value = form_data.get('field', '').strip()
        if not field_value:
            yield rx.toast.error("Field is required")
            return

        # Update item
        # await update_item(item_id, field_value)

        yield rx.toast.success("Item updated successfully")

# Form content
def my_form_content():
    return rx.vstack(
        rx.text("Field Name", size="2", weight="bold"),
        rx.input(
            name="field",
            placeholder="Enter value",
            default_value=MyFormState.form_field,
            required=True,
            width="100%"
        ),
        width="100%",
        spacing="1"
    )

# Create dialog
form_dialog_component(
    state=MyFormState,
    title=rx.cond(
        MyFormState.is_update_mode,
        "Update Item",
        "Create Item"
    ),
    description="Enter the item details below.",
    form_content=my_form_content(),
)'''

    return page_layout(
        "Dialog Components",
        "This page demonstrates various dialog components for user interactions, "
        "including basic dialogs, confirmation dialogs, and form dialogs.",
        # Basic dialog example
        example_tabs(
            example_component=basic_dialog_component,
            code=code1,
            title="dialog_header",
            description="A reusable header component for dialogs with title and close button.",
            func=dialog_header,
        ),
        # Confirm dialog example
        example_tabs(
            example_component=confirm_dialog_component,
            code=code2,
            title="confirm_dialog",
            description="A confirmation dialog for destructive actions with async action support.",
        ),
        # Form dialog example
        example_tabs(
            example_component=example3_component,
            code=code3,
            title="form_dialog_component",
            description="A form dialog component supporting both create and update modes.",
            func=form_dialog_component,
        ),
    )
