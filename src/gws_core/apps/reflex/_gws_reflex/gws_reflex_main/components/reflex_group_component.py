
from typing import List

import reflex as rx
from gws_core.space.space_dto import SpaceGroupDTO

from .reflex_user_components import user_inline_component


def group_inline_component(group: SpaceGroupDTO, size: str = "32px") -> rx.Component:
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
        size (str): Size of the icon/avatar circle (default: "32px")

    Returns:
        rx.Component: Horizontal stack with group icon/user and label

    Example:
        group_component = group_inline_component(group_dto)
        # Displays circular icon/user photo with label beside it
    """
    return rx.cond(
        group.user is not None,
        # If user exists, show user inline component
        user_inline_component(group.user, size),
        # Otherwise show people icon with group label
        rx.hstack(
            rx.icon(
                tag="users",
                size=16,
                color="var(--accent-10)",
            ),
            rx.text(
                group.label,
                size="2",
            ),
            spacing="2",
            align="center",
        ),
    )


def group_select(
    groups: List[SpaceGroupDTO],
    placeholder: str = "Select a group",
    name: str = None,
    disabled: bool = False,
    **kwargs,
) -> rx.Component:
    """Group select component for choosing from a list of groups.

    This component provides a dropdown select interface for choosing a group
    from a list. Each group is displayed using the group_inline_component,
    showing either the user's profile (for SINGLE_USER groups) or a people
    icon with the group label (for TEAM groups).

    Args:
        groups (List[SpaceGroupDTO]): List of group data transfer objects
        placeholder (str): Placeholder text shown when no group is selected
            (default: "Select a group")
        name (str): Optional name attribute for form submission

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
                    group_inline_component(group, size="24px"),
                    value=group.id,
                ),
            )
        ),
        name=name,
        disabled=disabled,
        **kwargs,
    )
