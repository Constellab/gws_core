from typing import List

import streamlit as st
from pandas import DataFrame

from gws_core.impl.table.table import Table


class TableInfo():
    id: int
    table: Table
    name: str
    original_name: str

    def __init__(self, id: int, table: Table, name: str, original_name: str = None):
        self.id = id
        self.table = table
        self.name = name
        if original_name is None:
            self.original_name = name
        else:
            self.original_name = original_name

    def get_dataframe(self) -> DataFrame:
        return self.table.get_data()

    def __str__(self):
        return self.name + f" ({self.id})"

    def __eq__(self, value):
        if value is None:
            return False
        if not isinstance(value, TableInfo):
            return False
        return self.id == value.id


class AutoMlState():

    TABLES_KEY = "tables"
    CURRENT_TABLE_KEY = "current_table"
    LAST_ID_KEY = "last_id"

    # Use to share the state of the select box for current table between pages
    # all pages uses same key
    SELECT_TABLE_KEY = "select_table"

    @classmethod
    def init(cls, table: Table, name: str):
        table_info = cls.add_table(table=table, name=name, set_current=True)
        cls.set_current_table(table_info.id)

    @classmethod
    def get_tables(cls) -> List[TableInfo]:
        return st.session_state.get(cls.TABLES_KEY, [])

    @classmethod
    def has_current_table(cls) -> bool:
        return cls.get_current_table() is not None

    @classmethod
    def add_table(cls, table: Table, name: str, set_current: bool = False, original_name: str = None) -> TableInfo:
        table_info = TableInfo(cls._get_new_id(), table, name, original_name)
        tables = cls.get_tables()
        tables.append(table_info)
        st.session_state[cls.TABLES_KEY] = tables

        if set_current:
            cls.set_current_table(table_info.id)
        return table_info

    @classmethod
    def get_current_table(cls) -> TableInfo:
        return st.session_state.get(cls.CURRENT_TABLE_KEY, None)

    @classmethod
    def get_current_table_index(cls) -> int:
        current_table = cls.get_current_table()
        tables = cls.get_tables()
        for i, table in enumerate(tables):
            if table.id == current_table.id:
                return i
        return 0

    @classmethod
    def _get_new_id(cls) -> int:
        last_id = st.session_state.get(cls.LAST_ID_KEY, 0)
        new_id = last_id + 1
        st.session_state[cls.LAST_ID_KEY] = new_id
        return new_id

    @classmethod
    def set_current_table(cls, id: int) -> TableInfo:
        tables = cls.get_tables()
        current_table = next((table for table in tables if table.id == id), None)
        if current_table is None:
            raise ValueError(f"Table with id {id} not found")
        st.session_state[cls.CURRENT_TABLE_KEY] = current_table
        return current_table
