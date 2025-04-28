
from typing import Callable, List, Literal, Optional, TypedDict

import streamlit as st

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.streamlit.components.streamlit_component_loader import \
    StreamlitComponentLoader


class StreamlitMenuButtonItemDTO(BaseModelDTO):
    key: str
    label: str
    material_icon: Optional[str] = None
    disabled: Optional[bool] = False
    children: Optional[List['StreamlitMenuButtonItemDTO']] = None
    divider: Optional[bool] = False
    color: Optional[Literal['primary', 'accent', 'warn']] = None
    has_handler: bool


class StreamlitMenuButtonItem():
    key: str
    label: str
    material_icon: Optional[str] = None
    disabled: Optional[bool] = False
    children: Optional[List['StreamlitMenuButtonItem']] = None
    on_click: Optional[Callable] = None
    divider: Optional[bool] = False
    color: Optional[Literal['primary', 'accent', 'warn']] = None

    def __init__(self, label: str, key: str = None, material_icon: str = None, disabled: bool = False,
                 children: List['StreamlitMenuButtonItem'] = None,
                 on_click: Callable = None, divider: bool = False,
                 color: Literal['primary', 'accent', 'warn'] = None):
        """ Create a menu button item

        :param label: Label of the item
        :type label: str
        :param key: unique key of the item, it should not change. It is used to
                    find button on click, defaults to None
        :type key: str, optional
        :param material_icon: Material icon name, defaults to None
        :type material_icon: str, optional
        :param disabled: If the item is disabled, defaults to False
        :type disabled: bool, optional
        :param children: List of children items, defaults to None
        :type children: List[StreamlitMenuButtonItem], optional
        :param on_click: Function to call when the item is clicked, defaults to None
        :type on_click: Callable, optional
        :param divider: If to show a divider before the item, defaults to False
        :type divider: bool, optional
        :param color: Color of the item, can be 'primary', 'accent' or 'warn', defaults to None
        :type color: Literal[primary, accent, warn], optional
        """
        self.label = label
        if key is not None:
            self.key = key
        else:
            self.key = label
        self.material_icon = material_icon
        self.disabled = disabled
        self.children = children
        self.on_click = on_click
        self.divider = divider
        self.color = color

    def add_child(self, child: 'StreamlitMenuButtonItem') -> None:
        """ Add a child to the item

        :param child: Child item to add
        :type child: StreamlitMenuButtonItem
        :return: The child item added
        :rtype: StreamlitMenuButtonItem
        """
        if self.children is None:
            self.children = []
        self.children.append(child)

    def add_children(self, children: List['StreamlitMenuButtonItem']) -> None:
        """ Add a child to the item

        :param child: Child item to add
        :type child: StreamlitMenuButtonItem
        """
        if self.children is None:
            self.children = []
        self.children.extend(children)

    def find_by_key(self, key: str) -> Optional['StreamlitMenuButtonItem']:
        if self.key == key:
            return self

        if self.children is not None:
            for child in self.children:
                found = child.find_by_key(key)
                if found is not None:
                    return found

        return None

    def to_dto(self) -> StreamlitMenuButtonItemDTO:
        """ Convert the item to a DTO

        :return: DTO of the item
        :rtype: StreamlitMenuButtonItemDTO
        """
        return StreamlitMenuButtonItemDTO(
            key=self.key,
            label=self.label, material_icon=self.material_icon, disabled=self.disabled,
            children=[child.to_dto() for child in self.children] if self.children else None, divider=self.divider,
            color=self.color,
            has_handler=self.on_click is not None)


class StreamlitMenuButtonValue(TypedDict):
    button_key: str
    # use to distinguish the different clicks
    # it is used to avoid the click to be processed twice
    # when the component is reloaded
    timestamp: int


class StreamlitMenuButton:
    """
    Streamlit component to create a menu button
    It is useful to create a menu button with multiple items.
    It supports children items.
    """

    _streamlit_component_loader = StreamlitComponentLoader("menu-button")

    _buttons: List[StreamlitMenuButtonItem] = None

    def __init__(self, key='streamlit-menu'):
        self.key = key
        self._buttons = []

    def add_button_item(self, button: StreamlitMenuButtonItem) -> None:
        self._buttons.append(button)

    def add_button_items(self, buttons: List[StreamlitMenuButtonItem]) -> None:
        """ Add a list of buttons to the menu button

        :param buttons: List of buttons to add
        :type buttons: List[StreamlitMenuButtonItem]
        """
        self._buttons.extend(buttons)

    def find_button_item_by_key(self, key: str) -> Optional[StreamlitMenuButtonItem]:
        """ Find a button by its id

        :param id: Id of the button to find
        :type id: str
        :return: Button found or None
        :rtype: Optional[StreamlitMenuButtonItem]
        """
        for button in self._buttons:
            found = button.find_by_key(key)
            if found is not None:
                return found

        return None

    def render(self, icon: str = 'more_vert', disabled: bool = False) -> StreamlitMenuButtonItem:
        """
        Render the menu button and return the button clicked

        :param icon: Icon to show on the button, defaults to 'more_vert'
        :type icon: str, optional
        :param disabled: If the menu button is disabled, defaults to False
        :type disabled: bool, optional
        :return: Button clicked
        :rtype: StreamlitMenuButtonItem
        """

        data = {
            'icon': icon,
            "disabled": disabled,
            "menu_items": [button.to_dto() for button in self._buttons],
        }

        component_value: StreamlitMenuButtonValue = self._streamlit_component_loader.call_component(
            data, key=self.key)

        if not component_value:
            return None

        # as the component value is stored in the session state, we compare the value
        # with the previous click value to avoid double click
        # if the timestamp has changed, it means a click was really triggered
        # if the timestamp is the same, it means the component was just reloaded but no click was triggered
        previous_click_key = '__' + self.key + '_previous_click__'
        previous_click: StreamlitMenuButtonValue = st.session_state.get(previous_click_key)

        # if the button was clicked
        if previous_click is None or previous_click.get('timestamp') != component_value.get('timestamp'):

            button_key = component_value.get('button_key')

            button = self.find_button_item_by_key(button_key)
            if button is None:
                raise Exception(f"[StreamlitMenuButton] Button with key '{button_key}' not found")

            if button.on_click is None:
                raise Exception(f"[StreamlitMenuButton] Button with key '{button_key}' has no on_click handler")

            button.on_click()

            # store the value in the session state to avoid double click
            st.session_state[previous_click_key] = component_value

            return button

        return None
