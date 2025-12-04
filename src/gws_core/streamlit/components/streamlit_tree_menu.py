from typing import List, Optional

import streamlit as st

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.streamlit.components.streamlit_component_loader import StreamlitComponentLoader


class StreamlitTreeMenuItemDTO(BaseModelDTO):
    id: str
    label: str
    material_icon: Optional[str] = None
    children: Optional[List["StreamlitTreeMenuItemDTO"]] = None
    disabled: Optional[bool] = False


class StreamlitTreeMenuItem:
    key: str
    label: str
    material_icon: Optional[str] = None
    children: Optional[List["StreamlitTreeMenuItem"]] = None
    disabled: Optional[bool] = False

    def __init__(
        self,
        label: str,
        key: str = None,
        material_icon: str = None,
        children: List["StreamlitTreeMenuItem"] = None,
        disabled: bool = False,
    ):
        """Create a menu button item

        :param label: Label of the item
        :type label: str
        :param key: unique key of the item, it should not change. It is used to
                    find button on click, defaults to None
        :type key: str, optional
        :param material_icon: Material icon name, defaults to None
        :type material_icon: str, optional
        :param children: List of children items, defaults to None
        :type children: List[StreamlitTreeMenuItem], optional
        :param disabled: If the item is disabled, defaults to False
        :type disabled: bool, optional
        """
        self.label = label
        if key is not None:
            self.key = key
        else:
            self.key = label
        self.material_icon = material_icon
        self.children = children
        self.disabled = disabled

    def add_child(self, child: "StreamlitTreeMenuItem") -> None:
        """Add a child to the item

        :param child: Child item to add
        :type child: StreamlitTreeMenuItemItem
        :return: The child item added
        :rtype: StreamlitTreeMenuItemItem
        """
        if self.children is None:
            self.children = []
        self.children.append(child)

    def add_children(self, children: List["StreamlitTreeMenuItem"]) -> None:
        """Add a list of children to the item

        :param children: List of child items to add
        :type children: List[StreamlitTreeMenuItemItem]
        """
        if self.children is None:
            self.children = []
        self.children.extend(children)

    def insert_child(self, index: int, child: "StreamlitTreeMenuItem") -> None:
        """Insert a child to the item

        :param index: Index of the child to insert
        :type index: int
        :param child: Child item to add
        :type child: StreamlitTreeMenuItemItem
        """
        if self.children is None:
            self.children = []
        if index >= len(self.children):
            raise Exception(f"[StreamlitTreeMenuItem] Child index {index} out of range")

        self.children.insert(index, child)

    def update_child(self, index: int, child: "StreamlitTreeMenuItem") -> None:
        """Update a child in the item

        :param index: Index of the child to update
        :type index: int
        :param child: Child item to add
        :type child: StreamlitTreeMenuItemItem
        """
        if self.children is None:
            raise Exception("[StreamlitTreeMenuItem] No children to update")
        if index >= len(self.children):
            raise Exception(f"[StreamlitTreeMenuItem] Child index {index} out of range")
        self.children[index] = child

    def remove_child_at(self, index: int) -> None:
        """Remove a child from the item

        :param index: Index of the child to remove
        :type index: int
        """
        if self.children is None:
            raise Exception("[StreamlitTreeMenuItem] No children to remove")
        if index >= len(self.children):
            raise Exception(f"[StreamlitTreeMenuItem] Child index {index} out of range")
        self.children.pop(index)

    def find_by_key(self, key: str) -> Optional["StreamlitTreeMenuItem"]:
        if self.key == key:
            return self

        if self.children is not None:
            for child in self.children:
                found = child.find_by_key(key)
                if found is not None:
                    return found

        return None

    def to_dto(self) -> StreamlitTreeMenuItemDTO:
        """Convert the item to a DTO

        :return: DTO of the item
        :rtype: StreamlitTreeMenuItemItemDTO
        """
        return StreamlitTreeMenuItemDTO(
            id=self.key,
            label=self.label,
            material_icon=self.material_icon,
            children=[child.to_dto() for child in self.children] if self.children else None,
            disabled=self.disabled,
        )


class StreamlitTreeMenu:
    """
    Streamlit component to create a menu button
    It is useful to create a menu button with multiple items.
    It supports children items.
    """

    _streamlit_component_loader = StreamlitComponentLoader("tree-menu")

    _items: List[StreamlitTreeMenuItem] = None

    def __init__(self, key="tree-menu"):
        self.key = key
        self._items = []
        # init component state in session state
        if key not in st.session_state:
            st.session_state[self.key] = {"item_key": None}  # for backward compatibility

    def add_item(self, item: StreamlitTreeMenuItem) -> None:
        """Add an item to the tree menu.

        :param item: Item to add to the tree menu
        :type item: StreamlitTreeMenuItem
        """
        self._items.append(item)

    def add_items(self, items: List[StreamlitTreeMenuItem]) -> None:
        """Add a list of items to the tree menu.

        :param items: List of items to add
        :type items: List[StreamlitTreeMenuItem]
        """
        self._items.extend(items)

    def set_selected_item(self, item_key: str) -> None:
        """Override the current value and set the selected item in the tree menu.

        :param item_key: Key of the item to set as selected
        :type item_key: str
        :raises Exception: If the item with the specified key is not found
        """
        item = self.find_item_by_key(item_key)
        if item is None:
            raise Exception(f"[StreamlitTreeMenu] Item with key '{item_key}' not found")

        # update the inner state of the component, update the sub dict value
        # directly to avoid streamlit error
        st.session_state[self.key]["item_key"] = item.key  # for backward compatibility

    def set_default_selected_item(self, item_key: str) -> None:
        """Set the default selected item in the tree menu.

        If there is a selected item already, it will not be changed.

        :param item_key: Key of the item to set as default selected
        :type item_key: str
        """

        if self.get_selected_item() is None:
            self.set_selected_item(item_key)

    def get_selected_item(self) -> Optional[StreamlitTreeMenuItem]:
        """Get the selected item in the tree menu.

        :return: Selected item or None if no item is selected
        :rtype: Optional[StreamlitTreeMenuItem]
        """
        # item_key = st.session_state.get(self._get_state_key(), None)
        item_key = st.session_state[self.key].get("item_key")
        if item_key is None:
            return None

        return self.find_item_by_key(item_key)

    def find_item_by_key(self, key: str) -> Optional[StreamlitTreeMenuItem]:
        """Find an item by its key.

        :param key: Key of the item to find
        :type key: str
        :return: Item found or None if not found
        :rtype: Optional[StreamlitTreeMenuItem]
        """
        for item in self._items:
            found = item.find_by_key(key)
            if found is not None:
                return found

        return None

    def render(self) -> StreamlitTreeMenuItem | None:
        """Render the tree menu and return the selected item.

        :return: Selected item or None if no item is selected
        :rtype: StreamlitTreeMenuItem | None
        """

        selected_item = self.get_selected_item()

        data = {
            "tree_items": [item.to_dto() for item in self._items],
            "selected_item": selected_item.key if selected_item else None,
        }

        self._streamlit_component_loader.call_component(data, key=self.key)

        return self.get_selected_item()
