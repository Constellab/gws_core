

from typing import Type

from pandas import DataFrame

from gws_core.impl.table.table import Table
from gws_core.io.io_validator import IOValidator
from gws_core.resource.resource import Resource


class TableNumberValidator(IOValidator):

    resource_type: Type[Resource] = Table

    def validate(self, resource: Table) -> None:

        dataframe: DataFrame = resource.get_data()

        # check that all columns are numeric and if not raise an exception
        # with all columns that are not numeric
        none_numeric_columns = dataframe.select_dtypes(exclude=['number']).columns.tolist()

        if len(none_numeric_columns) > 0:
            raise Exception(
                f"Columns {none_numeric_columns} are not numeric. Please check your data.")
