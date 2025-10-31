from abc import abstractmethod

import reflex as rx


class ConfirmDialogState(rx.State, mixin=True):
    """Mixin state for managing a confirmation dialog.

    This state can be mixed into other states to provide dialog open/close functionality.
    """

    dialog_opened: bool = False

    @rx.event
    def open_dialog(self):
        """Open the confirmation dialog."""
        self.dialog_opened = True

    @rx.event
    def close_dialog(self):
        """Close the confirmation dialog."""
        self.dialog_opened = False


    @abstractmethod
    async def confirm_action(self):
        """Perform the action to confirm."""
        pass

def confirm_dialog(
    title: str,
    content: str,
    state: ConfirmDialogState,
) -> rx.Component:
    """Reusable confirmation dialog component.

    This component creates an alert dialog that asks for user confirmation before
    performing an action. It displays a title, content message, and action buttons.

    Args:
        state (ConfirmDialogState): The state object managing the dialog's behavior.
        confirm_color_scheme (str): Color scheme for the confirm button (default: "red")
        open_state (rx.Var): Optional state variable to control dialog visibility.
                             If not provided, dialog must be controlled externally.

    Returns:
        rx.Component: Alert dialog component
    """

    return rx.alert_dialog.root(
        rx.alert_dialog.content(
            rx.alert_dialog.title(title),
            rx.alert_dialog.description(content, margin_bottom="1rem"),
            rx.flex(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=state.close_dialog,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        "Confirm",
                        on_click=state.confirm_action,
                    ),
                ),
                spacing="3",
                justify="end",
            ),
        ),
        open=state.dialog_opened,
    )
