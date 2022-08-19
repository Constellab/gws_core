# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, Optional

from fastapi.param_functions import Depends
from gws_core.core.classes.search_builder import SearchParams
from gws_core.resource.view_config.view_config_service import ViewConfigService
from gws_core.user.auth_service import AuthService
from gws_core.user.user_dto import UserData

from ...core_app import core_app


@core_app.post("/view-config/search", tags=["Report"],
               summary="Search available view config")
def search(search_dict: SearchParams,
           page: Optional[int] = 1,
           number_of_items_per_page: Optional[int] = 20,
           _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ViewConfigService.search(search_dict,
                                    page, number_of_items_per_page).to_json()


@core_app.post("/view-config/search/report/{report_id}", tags=["Report"],
               summary="Search available view config for a report")
def search_for_report(report_id: str,
                      search_dict: SearchParams,
                      page: Optional[int] = 1,
                      number_of_items_per_page: Optional[int] = 20,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ViewConfigService.search_for_report(report_id, search_dict,
                                               page, number_of_items_per_page).to_json()
