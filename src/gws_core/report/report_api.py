# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import List, Optional

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.param_functions import Depends
from fastapi.responses import FileResponse

from gws_core.core.model.model_dto import PageDTO
from gws_core.experiment.experiment_dto import ExperimentDTO

from ..core.classes.search_builder import SearchParams
from ..core_app import core_app
from ..report.report_dto import (ReportDTO, ReportFullDTO, ReportImageDTO,
                                 ReportSaveDTO)
from ..report.report_service import ReportService
from ..user.auth_service import AuthService


@core_app.post("/report", tags=["Report"], summary="Create a report for an experiment")
def create(report_dto: ReportSaveDTO, _=Depends(AuthService.check_user_access_token)) -> ReportDTO:
    return ReportService.create(report_dto).to_dto()


@core_app.post("/report/experiment/{experiment_id}", tags=["Report"], summary="Create a report for an experiment")
def create_for_experiment(experiment_id: str,
                          report_dto: ReportSaveDTO,
                          _=Depends(AuthService.check_user_access_token)) -> ReportDTO:
    return ReportService.create(report_dto, [experiment_id]).to_dto()


@core_app.put("/report/{report_id}", tags=["Report"], summary="Update a report information")
def update(report_id: str, report_dto: ReportSaveDTO, _=Depends(AuthService.check_user_access_token)) -> ReportDTO:
    return ReportService.update(report_id, report_dto).to_dto()


@core_app.put("/report/{report_id}/title", tags=["Report"],
              summary="Update the title of a report")
def update_title(report_id: str,
                 body: dict,
                 _=Depends(AuthService.check_user_access_token)) -> ReportDTO:
    return ReportService.update_title(report_id, body["title"]).to_dto()


@core_app.put("/report/{report_id}/project", tags=["Report"],
              summary="Update the project of a report")
def update_project(report_id: str,
                   body: dict,
                   _=Depends(AuthService.check_user_access_token)) -> ReportDTO:
    return ReportService.update_project(report_id, body["project_id"]).to_dto()


@core_app.put("/report/{report_id}/content", tags=["Report"], summary="Update a report content")
def update_content(report_id: str, content: dict, _=Depends(AuthService.check_user_access_token)) -> ReportDTO:
    return ReportService.update_content(report_id, content).to_dto()


@core_app.put("/report/{report_id}/content/add-view/{view_config_id}", tags=["Report"],
              summary="Add a view to the report")
def add_view_to_content(report_id: str, view_config_id: str,
                        _=Depends(AuthService.check_user_access_token)) -> ReportDTO:
    return ReportService.add_view_to_content(report_id, view_config_id).to_dto()


@core_app.delete("/report/{report_id}", tags=["Report"], summary="Delete a report")
def delete(report_id: str, _=Depends(AuthService.check_user_access_token)) -> None:
    ReportService.delete(report_id)


@core_app.put(
    "/report/{report_id}/add-experiment/{experiment_id}", tags=["Report"],
    summary="Add an experiment to the report")
def add_experiment(report_id: str, experiment_id: str, _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return ReportService.add_experiment(report_id, experiment_id).to_dto()


@core_app.delete(
    "/report/{report_id}/remove-experiment/{experiment_id}", tags=["Report"],
    summary="Remove an experiment")
def remove_experiment(
        report_id: str, experiment_id: str, _=Depends(AuthService.check_user_access_token)) -> None:
    ReportService.remove_experiment(report_id, experiment_id)


@core_app.put("/report/{report_id}/validate/{project_id}", tags=["Report"], summary="Validate the report")
def validate(report_id: str, project_id: Optional[str] = None,
             _=Depends(AuthService.check_user_access_token)) -> ReportFullDTO:
    return ReportService.validate_and_send_to_space(report_id, project_id).to_full_dto()


@core_app.put('/report/{report_id}/sync-with-space', tags=["Report"], summary="Sync the report with space")
def sync_with_space(report_id: str,
                    _=Depends(AuthService.check_user_access_token)) -> ReportFullDTO:
    return ReportService.synchronize_with_space_by_id(report_id).to_full_dto()


################################################# Image ########################################

@core_app.post("/report/image", tags=["Report"], summary="Upload an object")
def upload_image(image: UploadFile = FastAPIFile(...),
                 _=Depends(AuthService.check_user_access_token)) -> ReportImageDTO:
    return ReportService.upload_image(image)


@core_app.get("/report/image/{filename}", tags=["Report"], summary="Get an image of the report")
def get_image(filename: str,
              _=Depends(AuthService.check_user_access_token)) -> FileResponse:
    return ReportService.get_image_file_response(filename)


@core_app.delete("/report/image/{filename}", tags=["Report"], summary="Delete an object")
def delete_image(filename: str,
                 _=Depends(AuthService.check_user_access_token)) -> None:
    ReportService.delete_image(filename)

################################################# GET ########################################


@core_app.get("/report/{id}", tags=["Report"], summary="Get a report", response_model=None)
def get_by_id(id: str, _=Depends(AuthService.check_user_access_token)) -> ReportFullDTO:
    return ReportService.get_by_id_and_check(id).to_full_dto()


@core_app.get("/report/experiment/{experiment_id}", tags=["Report"],
              summary="Find reports of an experiment", response_model=None)
def get_by_experiment(experiment_id: str, _=Depends(AuthService.check_user_access_token)) -> List[ReportDTO]:
    reports = ReportService.get_by_experiment(experiment_id)
    return [report.to_dto() for report in reports]


@core_app.get("/report/{report_id}/experiments", tags=["Report"],
              summary="Find experiments of a report", response_model=None)
def get_experiment_by_report(
        report_id: str, _=Depends(AuthService.check_user_access_token)) -> List[ExperimentDTO]:
    experiments = ReportService.get_experiments_by_report(report_id)
    return [experiment.to_dto() for experiment in experiments]


@core_app.post("/report/search", tags=["Report"], summary="Advanced search for reports")
def advanced_search(search_dict: SearchParams,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[ReportDTO]:
    """
    Advanced search on experiment
    """

    return ReportService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/report/search-name/{name}", tags=["Report"],
              summary="Search for report by name")
def search_by_name(name: str,
                   page: Optional[int] = 1,
                   number_of_items_per_page: Optional[int] = 20,
                   _=Depends(AuthService.check_user_access_token)) -> PageDTO[ReportDTO]:
    return ReportService.search_by_name(name, page, number_of_items_per_page).to_dto()


@core_app.get("/report/resource/{resource_id}", tags=["Report"],
              summary="Get the list of report by resource")
def get_by_resource(resource_id: str,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[ReportDTO]:

    return ReportService.get_by_resource(
        resource_id=resource_id,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_dto()


################################################# ARCHIVE ########################################
@core_app.put("/report/{id}/archive", tags=["Report"], summary="Archive a report")
def archive(id: str, _=Depends(AuthService.check_user_access_token)) -> ReportDTO:
    return ReportService.archive_report(id).to_dto()


@core_app.put("/report/{id}/unarchive", tags=["Report"], summary="Unarchive a report")
def unarchive(id: str, _=Depends(AuthService.check_user_access_token)) -> ReportDTO:
    return ReportService.unarchive_report(id).to_dto()
