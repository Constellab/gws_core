

import sqlite3
from typing import List

from pandas import read_sql_query

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.impl.file.file import File
from gws_core.impl.table.table import Table
from gws_core.impl.table.view.table_view import TableView
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.view.view import View
from gws_core.resource.view.view_decorator import view


@resource_decorator("SqliteResource")
class SqliteResource(File):

    __default_extensions__: List[str] = ['db', 'sqlite', 'sqlite3']

    def get_table_names(self) -> List[str]:
        table = self.execute_select("SELECT name FROM sqlite_master WHERE type='table';")
        return table.get_column_data("name")

    def select_table(self, table_name: str) -> Table:
        return self.execute_select("SELECT * FROM " + table_name + ";")

    def execute_select(self, query: str) -> Table:
        sqlite_path = self.path
        if not self.exists():
            raise Exception("The sqlite file does not exist")

        conn = sqlite3.connect(sqlite_path)

        # Create a pandas DataFrame by fetching the entire table from the database
        df = read_sql_query(query, conn)

        # Close the database connection
        conn.close()
        return Table(df)

    def _get_table_names_view(self) -> TableView:
        # Extract the table names from the fetched data
        table_names = self.get_table_names()
        table_view = TableView(Table(table_names))
        table_view.set_title("Tables names")
        return table_view

    def _get_select_table_view(self, table_name: str) -> TableView:
        table_view = TableView(self.select_table(table_name))
        table_view.set_title('Table - ' + table_name)
        return table_view

    @view(view_type=View, hide=True)
    def view_as_json(self, params: ConfigParams) -> View:
        pass

    @view(view_type=View, hide=True)
    def view_content_as_str(self, params: ConfigParams) -> View:
        pass

    @view(view_type=TableView, human_name="View content", short_description="Show content of the database", default_view=True)
    def default_view(self, params: ConfigParams) -> TableView:
        """ If there is only one table in the database, show it by default
            Otherwise show the list of tables
        """
        # Extract the table names from the fetched data
        table_names = self.get_table_names()

        if len(table_names) == 0:
            raise Exception("The sqlite file does not contain any table")

        if len(table_names) == 1:
            return self._get_select_table_view(table_names[0])

        return self._get_table_names_view()

    @view(view_type=TableView, human_name="Table names", short_description="List the tables of the database", default_view=False)
    def get_table_names_view(self, params: ConfigParams) -> TableView:
        return self._get_table_names_view()

    @view(view_type=TableView, human_name="View table", short_description="Show the content of a table", default_view=False,
          specs=ConfigSpecs({'table_name': StrParam(human_name="Table name", short_description="Name of the table to show")}))
    def select_table_view(self, params: ConfigParams) -> TableView:
        return self._get_select_table_view(params["table_name"])

    @view(view_type=TableView, human_name="Execute query", short_description="Show the result of a select query",
          default_view=False, specs=ConfigSpecs({'query': StrParam(human_name="Query", short_description="Query to execute")}))
    def execute_select_view(self, params: ConfigParams) -> TableView:
        query = params["query"]
        table_view = TableView(self.execute_select(query))
        table_view.set_title(query)
        return table_view
