from typing import Literal

import reflex as rx

from gws_core.space.space_dto import SpaceGroupDTO

from .reflex_user_components import user_inline_component


def group_inline_component(
    group: SpaceGroupDTO, size: Literal["small", "normal"] = "normal"
) -> rx.Component:
    """Group inline component that displays group icon/user and label horizontally.

    This component displays a group's representation alongside its label in a
    horizontal layout. If the group has an associated user (SINGLE_USER type),
    it displays the user's inline component. Otherwise, it shows a people icon
    with the group label.

    Args:
        group (SpaceGroupDTO): Group data transfer object containing:
            - label: Group's display name
            - user: Optional associated user for SINGLE_USER type groups
            - type: Group type (SINGLE_USER or TEAM)
        size (Literal["small", "normal"]): Size of the icon/avatar - "small" (24px) or "normal" (32px, default)

    Returns:
        rx.Component: Horizontal stack with group icon/user and label

    Example:
        group_component = group_inline_component(group_dto, size="small")
        # Displays circular icon/user photo with label beside it
    """
    # Determine icon size and font size based on size parameter
    icon_size = 16 if size == "small" else 20
    font_size = "12px" if size == "small" else "14px"

    return rx.cond(
        group.user,
        # If user exists, show user inline component
        user_inline_component(group.user, size),
        # Otherwise show people icon with group label
        rx.hstack(
            rx.icon(
                tag="users",
                size=icon_size,
                margin_left="6px",
                margin_right="8px",
            ),
            rx.text(
                group.label,
                font_size=font_size,
            ),
            spacing="2",
            align="center",
        ),
    )


def group_select(
    groups: list[SpaceGroupDTO],
    placeholder: str = "Select a group",
    name: str = None,
    disabled: bool = False,
    **kwargs,
) -> rx.Component:
    """Group select component for choosing from a list of groups.

    This component provides a dropdown select interface for choosing a group
    from a list. Each group is displayed using the group_inline_component with
    small size, showing either the user's profile (for SINGLE_USER groups) or
    a people icon with the group label (for TEAM groups).

    Args:
        groups (List[SpaceGroupDTO]): List of group data transfer objects
        placeholder (str): Placeholder text shown when no group is selected
            (default: "Select a group")
        name (str): Optional name attribute for form submission
        disabled (bool): Whether the select is disabled (default: False)
        **kwargs: Additional props to pass to the select.root component

    Returns:
        rx.Component: Select dropdown with group options

    Example:
        select = group_select(
            groups=group_list,
            placeholder="Choose a team",
            name="team_id"
        )
    """
    return rx.select.root(
        rx.select.trigger(placeholder=placeholder, width="100%"),
        rx.select.content(
            rx.foreach(
                groups,
                lambda group: rx.select.item(
                    group_inline_component(group, size="small"),
                    value=group.id,
                ),
            )
        ),
        name=name,
        disabled=disabled,
        **kwargs,
    )
