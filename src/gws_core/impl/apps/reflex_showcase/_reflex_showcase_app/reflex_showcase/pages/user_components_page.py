"""User components demo page for the Reflex showcase app."""

import reflex as rx
from gws_core.user.user_dto import UserDTO
from gws_reflex_main import (ReflexMainState, user_inline_component,
                             user_profile_picture, user_select)

from ..components import example_tabs, page_layout


class UserComponentsPageState(ReflexMainState):
    """State for the user components page."""

    selected_user_id: str = ""

    # Create fake users for demonstration
    fake_users = [
        UserDTO(
            id="1",
            email="alice.wonder@example.com",
            first_name="Alice",
            last_name="Wonder",
            photo=None,
        ),
        UserDTO(
            id="2",
            email="bob.smith@example.com",
            first_name="Bob",
            last_name="Smith",
            photo=None,
        ),
        UserDTO(
            id="3",
            email="charlie.brown@example.com",
            first_name="Charlie",
            last_name="Brown",
            photo=None,
        ),
    ]

    @rx.event
    def handle_user_select(self, value: str):
        """Handle user selection from dropdown."""
        self.selected_user_id = value

    @rx.var
    def first_user(self) -> UserDTO:
        """Get the first user from the fake users list."""
        return self.fake_users[0]


def user_components_page() -> rx.Component:
    """Render the user components demo page."""

    # Example 1: user_profile_picture
    example1_component = rx.vstack(
        rx.heading("Normal Size", size="4", margin_bottom="0.5em"),
        rx.hstack(
            user_profile_picture(UserComponentsPageState.first_user, size="normal"),
            spacing="4",
        ),
        rx.heading("Small Size", size="4", margin_top="1em", margin_bottom="0.5em"),
        rx.hstack(
            user_profile_picture(UserComponentsPageState.first_user, size="small"),
            spacing="4",
        ),
        align="start",
    )

    code1 = """from gws_reflex_main import user_profile_picture
from gws_core.user.user_dto import UserDTO

# Create a user DTO
user = UserDTO(
    id="1",
    email="alice.wonder@example.com",
    first_name="Alice",
    last_name="Wonder",
    photo='https://cdn-icons-png.flaticon.com/512/10438/10438146.png',
)

# Display user profile picture
user_profile_picture(user, size="normal")  # 32px
user_profile_picture(user, size="small")   # 24px"""

    # Example 2: user_inline_component
    example2_component = rx.vstack(
        rx.heading("Normal Size", size="4", margin_bottom="0.5em"),
        rx.vstack(
            user_inline_component(UserComponentsPageState.first_user, size="normal"),
            spacing="3",
            align="start",
        ),
        rx.heading("Small Size", size="4", margin_top="1em", margin_bottom="0.5em"),
        rx.vstack(
            user_inline_component(UserComponentsPageState.first_user, size="small"),
            spacing="3",
            align="start",
        ),
        align="start",
    )

    code2 = """from gws_reflex_main import user_inline_component
from gws_core.user.user_dto import UserDTO

# Create a user DTO
user = UserDTO(
    id="1",
    email="alice.wonder@example.com",
    first_name="Alice",
    last_name="Wonder",
    photo='https://cdn-icons-png.flaticon.com/512/10438/10438146.png',
)

# Display user profile picture with name
user_inline_component(user, size="normal")  # 32px avatar, 14px text
user_inline_component(user, size="small")   # 24px avatar, 12px text"""

    # Example 3: user_select
    example3_component = rx.vstack(
        rx.text("Select a user from the dropdown:", margin_bottom="0.5em"),
        user_select(
            users=UserComponentsPageState.fake_users,
            placeholder="Select a user",
            name="user_select",
            width="300px",
            on_change=UserComponentsPageState.handle_user_select,
        ),
        rx.cond(
            UserComponentsPageState.selected_user_id != "",
            rx.box(
                rx.text(f"Selected user ID: {UserComponentsPageState.selected_user_id}"),
                margin_top="1em",
            ),
        ),
        align="start",
    )

    code3 = """from gws_reflex_main import user_select, ReflexMainState
from gws_core.user.user_dto import UserDTO
import reflex as rx

class MyState(ReflexMainState):
    selected_user_id: str = ""

    @rx.event
    def handle_user_select(self, value: str):
        self.selected_user_id = value

# Create list of users
users = [
    UserDTO(id="1", email="alice@example.com",
            first_name="Alice", last_name="Wonder", photo='https://cdn-icons-png.flaticon.com/512/10438/10438146.png'),
    UserDTO(id="2", email="bob@example.com",
            first_name="Bob", last_name="Smith", photo='https://cdn-icons-png.flaticon.com/512/10438/10438146.png'),
]

# Display user select dropdown
user_select(
    users=users,
    placeholder="Select a user",
    name="user_select",
    width="300px",
    on_change=MyState.handle_user_select,
)"""

    return page_layout(
        "User Components",
        "This page demonstrates user-related components for displaying user avatars, "
        "names, and selection dropdowns.",

        # user_profile_picture example
        example_tabs(
            example_component=example1_component,
            code=code1,
            title="user_profile_picture",
            description="Displays a user's profile picture or initials in a circular avatar.",
            func=user_profile_picture,
        ),

        # user_inline_component example
        example_tabs(
            example_component=example2_component,
            code=code2,
            title="user_inline_component",
            description="Displays a user's avatar with their full name in a horizontal layout.",
            func=user_inline_component,
        ),

        # # user_select example
        example_tabs(
            example_component=example3_component,
            code=code3,
            title="user_select",
            description="A dropdown select component for choosing users from a list.",
            func=user_select,
        ),
    )
