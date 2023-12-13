# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Dict

from fastapi import Depends

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.table.resource_table_service import (ResourceTableService,
                                                        TableChart)
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.user.auth_service import AuthService

from ...core_controller import core_app


class CallChartTable(BaseModelDTO):
    table_view_name: str
    table_config_values: Dict[str, Any]
    chart_type: TableChart
    chart_config_values: Dict[str, Any]


@core_app.post("/resource-table/{id}/call-chart", tags=["Resource"],
               summary="Call a chart view on a table view")
def call_chart_on_table(id: str,
                        call_chart_table: CallChartTable,
                        _=Depends(AuthService.check_user_access_token)) -> CallViewResultDTO:
    """Method to call a chart on a table from the table view

    """
    return ResourceTableService.call_table_chart(resource_id=id,
                                                 table_view_name=call_chart_table.table_view_name,
                                                 table_config_values=call_chart_table.table_config_values,
                                                 chart_type=call_chart_table.chart_type,
                                                 chart_config_values=call_chart_table.chart_config_values).to_dto()
