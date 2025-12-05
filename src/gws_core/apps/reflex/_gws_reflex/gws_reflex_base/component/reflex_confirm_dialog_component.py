import traceback
from collections.abc import AsyncGenerator, Callable

import reflex as rx

ConfirmDialogAction = Callable[[], AsyncGenerator]


class ConfirmDialogState(rx.State):
    """State for managing a confirmation dialog with async action support.

    This state provides a reusable confirmation dialog that can be controlled from other states.
    The dialog displays a title, content message, and executes an async action upon confirmation.

    IMPORTANT: The `open_dialog` method must be called from another state (backend), not directly
    from the frontend. This ensures proper state management and action execution.

    No need to declare the dialog component in your page/component, as it is imported in the main_component
    to be globally available.

    Usage Example:
        ```python
        # In your state class
        class MyState(ReflexMainState):

            @rx.event
            async def open_delete_confirmation(self, item_id: str):
                '''Open the delete confirmation dialog from your state.'''
                # Get the confirm dialog state
                confirm_dialog_state = await self.get_state(ConfirmDialogState)

                # Open the dialog with title, content, and action
                confirm_dialog_state.open_dialog(
                    title="Delete Item",
                    content="Are you sure you want to delete this item?",
                    action= lambda: self.delete_action(item_id)
                )

            # Define the action to perform when user confirms
            async def delete_action(self, item_id: str):
                '''This action will be executed when user clicks Confirm.'''
                with await self.authenticate_user():
                    service = MyService()
                    service.delete_item(item_id)

                yield rx.toast.success("Item deleted successfully")
                yield rx.redirect("/items")

        # In your component
        def my_component():
            return rx.fragment(
                rx.button(
                    "Delete",
                    on_click=MyState.open_delete_confirmation(item_id)
                ),
                # Add the confirm_dialog2 component to your page
                confirm_dialog2()
            )
        ```

    Advanced Example with Closures:
        ```python
        @rx.event
        async def open_remove_user_dialog(self, user: UserDTO):
            '''Example showing how to capture variables in the action closure.'''
            confirm_dialog_state = await self.get_state(ConfirmDialogState)

            # Capture variables in local scope for the closure
            user_id = user.id
            user_name = f"{user.first_name} {user.last_name}"

            async def remove_user_action():
                '''Action with captured variables from outer scope.'''
                with await self.authenticate_user():
                    service = UserService()
                    service.remove_user(user_id)

                # Reload data after action
                await self.reload_users()

                yield rx.toast.success(f"{user_name} removed successfully")

            confirm_dialog_state.open_dialog(
                title="Remove User",
                content=f"Are you sure you want to remove {user_name}?",
                action=remove_user_action
            )
        ```

    Note:
        - The action must be an async generator function (use `yield` for events)
        - The dialog automatically manages loading state during action execution
        - Errors in the action are caught and displayed as toast notifications
        - The dialog closes automatically after successful action execution
    """

    dialog_opened: bool = False
    is_loading: bool = False

    title: str = ""
    content: str = ""

    _action: ConfirmDialogAction

    def open_dialog(self, title: str, content: str, action: ConfirmDialogAction):
        """Open the confirmation dialog."""
        self.title = title
        self.content = content
        self._action = action
        self.dialog_opened = True

    @rx.event
    def close_dialog(self):
        """Close the confirmation dialog."""
        self.dialog_opened = False

    @rx.event(background=True)  # type: ignore
    async def confirm_action(self):
        """Handle the confirmation action with loading state.

        This method manages the loading state and calls the abstract _on_confirm
        method implemented by subclasses.
        """
        async with self:
            self.is_loading = True

        try:
            async for event in self._action():
                yield event
        except Exception as e:
            # TODO to improve, this should use the Logger but
            # gws_core package is not available here
            print(f"Error in confirm_action: {e}")
            # print the exception for debugging
            traceback.print_exc()
            yield rx.toast.error(str(e))
            return
        finally:
            async with self:
                self.is_loading = False

        async with self:
            self.dialog_opened = False


def confirm_dialog() -> rx.Component:
    """Reusable confirmation dialog component.

    This component creates an alert dialog that asks for user confirmation before
    performing an action. It displays a title, content message, and action buttons.

    This dialog is imported in the main_component to be available globally.

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
            rx.alert_dialog.title(ConfirmDialogState.title),
            rx.alert_dialog.description(ConfirmDialogState.content, margin_bottom="1rem"),
            rx.flex(
                rx.alert_dialog.cancel(
                    rx.button(
                        "Cancel",
                        variant="soft",
                        color_scheme="gray",
                        on_click=ConfirmDialogState.close_dialog,
                        disabled=ConfirmDialogState.is_loading,
                    ),
                ),
                rx.alert_dialog.action(
                    rx.button(
                        rx.spinner(loading=ConfirmDialogState.is_loading),
                        "Confirm",
                        on_click=ConfirmDialogState.confirm_action,
                        disabled=ConfirmDialogState.is_loading,
                    ),
                ),
                spacing="3",
                justify="end",
            ),
        ),
        open=ConfirmDialogState.dialog_opened,
    )
