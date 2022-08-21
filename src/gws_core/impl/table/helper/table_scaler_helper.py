# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.impl.table.helper.dataframe_scaler_helper import (
    DataframeScalerHelper, DfAxisScaleFunction, DfScaleFunction)
from gws_core.impl.table.table import Table


class TableScalerHelper:

    @classmethod
    def scale(cls, table: Table, func: DfScaleFunction) -> Table:
        dataframe = DataframeScalerHelper.scale(table.get_data(), func)

        # keep the table types, and tags
        return table.create_sub_table(dataframe, row_tags=table.get_row_tags(), column_tags=table.get_column_tags())

    @classmethod
    def scale_by_columns(cls, table: Table, func: DfAxisScaleFunction) -> Table:
        dataframe = DataframeScalerHelper.scale_by_columns(table.get_data(), func)

        # keep the table types, and tags
        return table.create_sub_table(dataframe, row_tags=table.get_row_tags(), column_tags=table.get_column_tags())

    @classmethod
    def scale_by_rows(cls, table: Table, func: DfAxisScaleFunction) -> Table:
        dataframe = DataframeScalerHelper.scale_by_rows(table.get_data(), func)

        # keep the table types, and tags
        return table.create_sub_table(dataframe, row_tags=table.get_row_tags(), column_tags=table.get_column_tags())
