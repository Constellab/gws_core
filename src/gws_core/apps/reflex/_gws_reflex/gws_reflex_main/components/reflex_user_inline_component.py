
import reflex as rx
from gws_core.user.user_dto import UserDTO


def user_inline_component(user: UserDTO, size: str = "32px") -> rx.Component:
    """User inline component that displays user photo and name horizontally.

    This component displays a user's photo (or initials if no photo) alongside
    their full name in a horizontal layout. The photo is displayed as a circle
    with a border. If no photo is available, it shows the user's initials in a
    colored circle.

    Args:
        user (UserDTO): User data transfer object containing:
            - first_name: User's first name
            - last_name: User's last name
            - photo: Optional URL to user's photo
        size (str): Size of the avatar circle (default: "32px")

    Returns:
        rx.Component: Horizontal stack with user photo/initials and name

    Example:
        user_component = user_inline_component(user_dto)
        # Displays circular photo with name beside it
    """

    # Create avatar component - either with photo or initials
    avatar = rx.cond(
        user.photo,
        # If photo exists, show image
        rx.image(
            src=user.photo,
            width=size,
            height=size,
            border_radius="50%",
            object_fit="cover",
            border=f"2px solid var(--accent-10",
        ),
        # If no photo, show initials in colored circle
        rx.flex(
            rx.text(
                user.first_name[0].upper() + user.last_name[0].upper(),
                size="2",
                color="white",
            ),
            width=size,
            height=size,
            border_radius="50%",
            background_color="var(--accent-10)",
            align="center",
            justify="center",
        ),
    )

    return rx.hstack(
        avatar,
        rx.text(
            user.first_name + " " + user.last_name,
            size="2",
        ),
        spacing="2",
        align="center",
    )
