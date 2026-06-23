from __future__ import annotations

from enum import Enum

from gws_core.config.config_specs import ConfigSpecs
from gws_core.entity_action.entity_action_dto import (
    EntityActionButtonDTO,
    EntityActionColor,
    EntityActionLinkDTO,
    EntityActionMenuDTO,
)


class EntityActionKind(Enum):
    """The kind of an entity menu action.

    The values match the discriminant ``type`` of the action DTOs sent to the
    front (see :mod:`entity_action_dto`).
    """

    BUTTON = "button"
    LINK = "link"


class EntityAction:
    """Developer-facing builder for a single entity menu action.

    A plugin returns a list of these from ``get_actions``. Use the classmethod
    helpers (:meth:`button`, :meth:`link`) rather than building one directly.
    """

    kind: EntityActionKind
    text: str
    icon: str | None
    divider: bool
    color: EntityActionColor | None

    # button only
    action_name: str | None
    disabled: bool
    children: list[EntityAction] | None
    config_specs: ConfigSpecs | None

    # link only
    link_url: str | None

    def __init__(self, kind: EntityActionKind, text: str, icon: str | None = None,
                 divider: bool = False, color: EntityActionColor | None = None,
                 action_name: str | None = None, disabled: bool = False,
                 children: list[EntityAction] | None = None,
                 config_specs: ConfigSpecs | None = None,
                 link_url: str | None = None) -> None:
        """Build an entity action. Prefer the :meth:`button` / :meth:`link`
        classmethod helpers over calling this directly.

        :param kind: the action kind (button or link).
        :type kind: EntityActionKind
        :param text: the literal text displayed in the menu (no translation).
        :type text: str
        :param icon: optional Material icon name shown before the text.
        :type icon: str | None
        :param divider: if True, a divider is rendered before the action.
        :type divider: bool
        :param color: optional color of the menu item ('primary', 'accent' or
            'warn'). Defaults to the standard menu item color.
        :type color: EntityActionColor | None
        :param action_name: button only - short, plugin-local action name.
        :type action_name: str | None
        :param disabled: button only - if True, the button is disabled.
        :type disabled: bool
        :param children: button only - optional nested sub-menu actions.
        :type children: list[EntityAction] | None
        :param config_specs: button only - optional config specs. When set, the
            front renders a form from them on click and POSTs the collected
            values as the body of the execute request.
        :type config_specs: ConfigSpecs | None
        :param link_url: link only - the internal route the link points to.
        :type link_url: str | None
        """
        self.kind = kind
        self.text = text
        self.icon = icon
        self.divider = divider
        self.color = color
        self.action_name = action_name
        self.disabled = disabled
        self.children = children
        self.config_specs = config_specs
        self.link_url = link_url

    @classmethod
    def button(cls, action_name: str, text: str, icon: str | None = None,
               divider: bool = False, disabled: bool = False,
               color: EntityActionColor | None = None,
               children: list[EntityAction] | None = None,
               config_specs: ConfigSpecs | None = None) -> EntityAction:
        """Build a button action. Clicking it calls back the owning plugin.

        :param action_name: short, plugin-local action name. It is namespaced
            with the plugin id when converted to a DTO so the dispatch endpoint
            can route it back to the owning plugin. Must not contain a dot.
        :type action_name: str
        :param text: the literal text displayed on the button (no translation).
        :type text: str
        :param icon: optional Material icon name shown before the text.
        :type icon: str | None
        :param divider: if True, a divider is rendered before the button.
        :type divider: bool
        :param disabled: if True, the button is rendered disabled.
        :type disabled: bool
        :param color: optional color of the button ('primary', 'accent' or
            'warn'). Defaults to the standard menu item color.
        :type color: EntityActionColor | None
        :param children: optional nested actions rendered as a sub-menu.
        :type children: list[EntityAction] | None
        :param config_specs: optional config specs. When set, the front renders
            a form from them on click and POSTs the collected values as the body
            of the execute request; the plugin receives them in ``config_params``.
        :type config_specs: ConfigSpecs | None
        :return: the built button action.
        :rtype: EntityAction
        """
        return cls(kind=EntityActionKind.BUTTON, text=text, icon=icon,
                   divider=divider, color=color, action_name=action_name,
                   disabled=disabled, children=children,
                   config_specs=config_specs)

    @classmethod
    def link(cls, text: str, link_url: str, icon: str | None = None,
             divider: bool = False,
             color: EntityActionColor | None = None) -> EntityAction:
        """Build a link action pointing to an internal route.

        :param text: the literal text displayed on the link (no translation).
        :type text: str
        :param link_url: the internal route the link navigates to.
        :type link_url: str
        :param icon: optional Material icon name shown before the text.
        :type icon: str | None
        :param divider: if True, a divider is rendered before the link.
        :type divider: bool
        :param color: optional color of the link ('primary', 'accent' or
            'warn'). Defaults to the standard menu item color.
        :type color: EntityActionColor | None
        :return: the built link action.
        :rtype: EntityAction
        """
        return cls(kind=EntityActionKind.LINK, text=text, icon=icon,
                   divider=divider, color=color, link_url=link_url)

    def to_dto(self, plugin_id: str) -> EntityActionMenuDTO:
        """Convert to the DTO sent to the front.

        Button ``action_name`` is namespaced as ``<plugin_id>.<action_name>``,
        where ``plugin_id`` is itself ``<brick_name>.<plugin_name>``.

        :param plugin_id: the globally unique id of the owning plugin, used to
            namespace the action name of button actions.
        :type plugin_id: str
        :raises ValueError: if a field required by this action's kind is missing.
        :return: the menu item DTO matching this action's kind.
        :rtype: EntityActionMenuDTO
        """
        if not self.text:
            raise ValueError("An entity action must have a non-empty 'text'.")

        if self.kind == EntityActionKind.BUTTON:
            if not self.action_name:
                raise ValueError(
                    f"Button entity action '{self.text}' must have a non-empty "
                    "'action_name'."
                )
            children = (
                [child.to_dto(plugin_id) for child in self.children]
                if self.children else None
            )
            return EntityActionButtonDTO(
                text=self.text,
                action_name=f"{plugin_id}.{self.action_name}",
                icon=self.icon,
                divider=self.divider,
                disabled=self.disabled,
                color=self.color,
                children=children,
                config_specs=(
                    self.config_specs.to_dto() if self.config_specs else None
                ),
            )
        if self.kind == EntityActionKind.LINK:
            if not self.link_url:
                raise ValueError(
                    f"Link entity action '{self.text}' must have a non-empty "
                    "'link_url'."
                )
            return EntityActionLinkDTO(
                text=self.text, link=self.link_url, icon=self.icon,
                divider=self.divider, color=self.color,
            )
        raise ValueError(f"Unknown entity action kind '{self.kind}'")
