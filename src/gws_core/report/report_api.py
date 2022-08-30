# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List, Optional

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.param_functions import Depends
from fastapi.responses import FileResponse
from gws_core.core.classes.paginator import PaginatorDict
from gws_core.report.report_file_service import ReportImage

from ..core.classes.jsonable import ListJsonable
from ..core.classes.search_builder import SearchParams
from ..core_app import core_app
from ..experiment.experiment import Experiment
from ..project.project_dto import ProjectDto
from ..report.report import Report
from ..report.report_dto import ReportDTO
from ..report.report_service import ReportService
from ..user.auth_service import AuthService
from ..user.user_dto import UserData


@core_app.post("/report", tags=["Report"], summary="Create a report for an experiment")
def create(report_dto: ReportDTO, _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ReportService.create(report_dto).to_json()


@core_app.post("/report/experiment/{experiment_id}", tags=["Report"], summary="Create a report for an experiment")
def create_for_experiment(experiment_id: str,
                          report_dto: ReportDTO,
                          _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ReportService.create(report_dto, [experiment_id]).to_json()


@core_app.put("/report/{report_id}", tags=["Report"], summary="Update a report information")
def update(report_id: str, report_dto: ReportDTO, _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ReportService.update(report_id, report_dto).to_json()


@core_app.put("/report/{report_id}/content", tags=["Report"], summary="Update a report content")
def update_content(report_id: str, content: Dict, _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ReportService.update_content(report_id, content).to_json()


@core_app.put("/report/{report_id}/content/add-view/{view_config_id}", tags=["Report"],
              summary="Add a view to the report")
def add_view_to_content(report_id: str, view_config_id: str,
                        _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ReportService.add_view_to_content(report_id, view_config_id).to_json()


@core_app.delete("/report/{report_id}", tags=["Report"], summary="Delete a report")
def delete(report_id: str, _: UserData = Depends(AuthService.check_user_access_token)) -> None:
    ReportService.delete(report_id)


@core_app.put(
    "/report/{report_id}/add-experiment/{experiment_id}", tags=["Report"],
    summary="Add an experiment to the report")
def add_experiment(report_id: str, experiment_id: str, _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ReportService.add_experiment(report_id, experiment_id).to_json()


@core_app.delete(
    "/report/{report_id}/remove-experiment/{experiment_id}", tags=["Report"],
    summary="Remove an experiment")
def remove_experiment(
        report_id: str, experiment_id: str, _: UserData = Depends(AuthService.check_user_access_token)) -> None:
    ReportService.remove_experiment(report_id, experiment_id)


@core_app.put("/report/{report_id}/validate", tags=["Report"], summary="Validate the report")
def validate(report_id: str, project_dto: Optional[ProjectDto] = None,
             _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    return ReportService.validate_and_send_to_central(report_id, project_dto).to_json(deep=True)


@core_app.put('/report/{report_id}/sync-with-central', tags=["Report"], summary="Sync the report with central")
def sync_with_central(report_id: str,
                      _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    return ReportService.synchronize_with_central_by_id(report_id).to_json(deep=True)


################################################# Image ########################################

@core_app.post("/report/image", tags=["Report"], summary="Upload an object")
def upload_image(image: UploadFile = FastAPIFile(...),
                 _: UserData = Depends(AuthService.check_user_access_token)) -> ReportImage:
    return ReportService.upload_image(image)


@core_app.get("/report/image/{filename}", tags=["Report"], summary="Get an image of the report")
def get_image(filename: str,
              _: UserData = Depends(AuthService.check_user_access_token)) -> FileResponse:
    return ReportService.get_image_file_response(filename)


@core_app.delete("/report/image/{filename}", tags=["Report"], summary="Delete an object")
def delete_image(filename: str,
                 _: UserData = Depends(AuthService.check_user_access_token)) -> None:
    ReportService.delete_image(filename)

################################################# GET ########################################


@core_app.get("/report/{id}", tags=["Report"], summary="Get a report")
def get_by_id(id: str, _: UserData = Depends(AuthService.check_user_access_token)) -> List[Report]:
    return ReportService.get_by_id_and_check(id).to_json(deep=True)


@core_app.get("/report/experiment/{experiment_id}", tags=["Report"], summary="Find reports of an experiment")
def get_by_experiment(experiment_id: str, _: UserData = Depends(AuthService.check_user_access_token)) -> List[Report]:
    return ListJsonable(ReportService.get_by_experiment(experiment_id)).to_json()


@core_app.get("/report/{report_id}/experiments", tags=["Report"], summary="Find experiments of a report")
def get_experiment_by_report(
        report_id: str, _: UserData = Depends(AuthService.check_user_access_token)) -> List[Experiment]:
    return ListJsonable(ReportService.get_experiments_by_report(report_id)).to_json()


@core_app.post("/report/advanced-search", tags=["Report"], summary="Advanced search for reports")
async def advanced_search(search_dict: SearchParams,
                          page: Optional[int] = 1,
                          number_of_items_per_page: Optional[int] = 20,
                          _: UserData = Depends(AuthService.check_user_access_token)) -> Dict:
    """
    Advanced search on experiment
    """

    return ReportService.search(search_dict, page, number_of_items_per_page).to_json()


@core_app.get("/report/resource/{resource_id}", tags=["Report"],
              summary="Get the list of report by resource")
def get_by_resource(resource_id: str,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _: UserData = Depends(AuthService.check_user_access_token)) -> PaginatorDict:

    return ReportService.get_by_resource(
        resource_id=resource_id,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_json()
