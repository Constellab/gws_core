# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Dict, List, TypedDict

from fastapi import Depends
from gws_core.impl.table.resource_table_service import (ResourceTableService,
                                                        TableChart)
from gws_core.user.auth_service import AuthService
from gws_core.user.user_dto import UserData
from typing_extensions import TypedDict

from ...core_app import core_app
from ...task.transformer.transformer_type import TransformerDict


class CallChartTable(TypedDict):
    table_view_name: str
    table_config_values: Dict[str, Any]
    table_transformers: List[TransformerDict]
    chart_type: TableChart
    chart_config_values: Dict[str, Any]


@core_app.post("/resource-table/{id}/call-chart", tags=["Resource"],
               summary="Call a chart view on a table view")
async def call_chart_on_table(id: str,
                              call_chart_table: CallChartTable,
                              _: UserData = Depends(AuthService.check_user_access_token)) -> Any:
    """Method to call a chart on a table from the table view

    """
    return await ResourceTableService.call_table_chart(resource_id=id,
                                                       table_view_name=call_chart_table["table_view_name"],
                                                       table_config_values=call_chart_table["table_config_values"],
                                                       table_transformers=call_chart_table["table_transformers"],
                                                       chart_type=call_chart_table["chart_type"],
                                                       chart_config_values=call_chart_table["chart_config_values"])
