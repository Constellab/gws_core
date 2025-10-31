
from typing import List, Literal

import reflex as rx
from gws_core.user.user_dto import UserDTO


def user_profile_picture(user: UserDTO, size: Literal["small", "normal"] = "normal") -> rx.Component:
    """User profile picture component that displays a round photo or initials.

    This component displays a user's photo in a circular frame. If no photo is
    available, it shows the user's initials in a colored circle instead.

    :param user: User data transfer object containing first_name, last_name, and optional photo
    :param size: Size of the avatar - "small" (24px) or "normal" (32px), defaults to "normal"
    :return: Circular avatar with photo or initials
    """
    # Determine pixel size and font size based on size parameter
    pixel_size = "24px" if size == "small" else "32px"
    font_size = "11px" if size == "small" else "14px"

    # Create avatar component - either with photo or initials
    return rx.cond(
        user.photo,
        # If photo exists, show image
        rx.image(
            src=user.photo,
            width=pixel_size,
            height=pixel_size,
            border_radius="50%",
            object_fit="cover",
            border="2px solid var(--accent-10)",
            flex_shrink=0,
        ),
        # If no photo, show initials in colored circle
        rx.flex(
            rx.text(
                user.first_name[0].upper() + user.last_name[0].upper(),
                font_size=font_size,
                color="white",
            ),
            width=pixel_size,
            height=pixel_size,
            border_radius="50%",
            background_color="var(--accent-10)",
            align="center",
            justify="center",
            flex_shrink=0,
        ),
    )


def user_inline_component(user: UserDTO, size: Literal["small", "normal"] = "normal") -> rx.Component:
    """User inline component that displays user photo and name horizontally.

    This component displays a user's photo (or initials if no photo) alongside
    their full name in a horizontal layout. The photo is displayed as a circle
    with a border. If no photo is available, it shows the user's initials in a
    colored circle.

    :param user: User data transfer object containing first_name, last_name, and optional photo
    :param size: Size of the avatar - "small" (24px) or "normal" (32px), defaults to "normal"
    :return: Horizontal stack with user photo/initials and name
    """
    # Determine font size based on size parameter
    font_size = "12px" if size == "small" else "14px"

    return rx.hstack(
        user_profile_picture(user, size),
        rx.text(
            user.first_name + " " + user.last_name,
            font_size=font_size,
        ),
        spacing="2",
        align="center",
    )


def user_select(users: List[UserDTO],
                placeholder: str = "Select a user",
                name: str = None,
                disabled: bool = False,
                width: str = None,
                **kwargs) -> rx.Component:
    """User select component that allows selecting users from a list.

    This component displays a dropdown select with user profile pictures/initials
    and names. Users are displayed using the user_inline_component with small size.

    :param users: List of users to display in the select
    :param placeholder: Placeholder text when no user is selected, defaults to "Select a user"
    :param name: Name attribute for the select element
    :param disabled: Whether the select is disabled, defaults to False
    :param width: Width of the select component
    :param kwargs: Additional props to pass to the select.root component
    :return: User select component
    """

    return rx.select.root(
        rx.select.trigger(placeholder=placeholder, width=width),
        rx.select.content(
            rx.foreach(
                users,
                lambda user: rx.select.item(
                    user_inline_component(user, size="small"),
                    value=user.id,
                ),
            )
        ),
        name=name,
        disabled=disabled,
        **kwargs,
    )
