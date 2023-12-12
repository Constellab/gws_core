# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Optional

from fastapi import File as FastAPIFile
from fastapi import UploadFile
from fastapi.param_functions import Depends
from fastapi.responses import FileResponse

from gws_core.core.model.model_dto import PageDTO
from gws_core.report.report_dto import ReportImageDTO
from gws_core.report.template.report_template_dto import (
    ReportTemplateDTO, ReportTemplateFullDTO)
from gws_core.report.template.report_template_service import \
    ReportTemplateService

from ...core.classes.search_builder import SearchParams
from ...core_app import core_app
from ...user.auth_service import AuthService


@core_app.post("/report-template", tags=["Report template"], summary="Create an empty report template")
def create_empty(data: dict, _=Depends(AuthService.check_user_access_token)) -> ReportTemplateDTO:
    return ReportTemplateService.create_empty(data['title']).to_dto()


@core_app.post("/report-template/from-report", tags=["Report template"],
               summary="Create a report template from a report")
def create_from_report(data: dict, _=Depends(AuthService.check_user_access_token)) -> ReportTemplateDTO:
    return ReportTemplateService.create_from_report(data['report_id']).to_dto()


@core_app.put("/report-template/{report_id}/title", tags=["Report template"],
              summary="Update the title of a report")
def update_title(report_id: str,
                 body: dict,
                 _=Depends(AuthService.check_user_access_token)) -> ReportTemplateDTO:
    return ReportTemplateService.update_title(report_id, body["title"]).to_dto()


@core_app.put("/report-template/{report_id}/content", tags=["Report template"], summary="Update a report content")
def update_content(report_id: str, content: dict, _=Depends(AuthService.check_user_access_token)) -> ReportTemplateDTO:
    return ReportTemplateService.update_content(report_id, content).to_dto()


@core_app.delete("/report-template/{report_id}", tags=["Report template"], summary="Delete a report")
def delete(report_id: str, _=Depends(AuthService.check_user_access_token)) -> None:
    ReportTemplateService.delete(report_id)


################################################# Image ########################################

@core_app.post("/report-template/image", tags=["Report template"], summary="Upload an object")
def upload_image(image: UploadFile = FastAPIFile(...),
                 _=Depends(AuthService.check_user_access_token)) -> ReportImageDTO:
    return ReportTemplateService.upload_image(image)


@core_app.get("/report-template/image/{filename}", tags=["Report template"], summary="Get an image of the report")
def get_image(filename: str,
              _=Depends(AuthService.check_user_access_token)) -> FileResponse:
    return ReportTemplateService.get_image_file_response(filename)


@core_app.delete("/report-template/image/{filename}", tags=["Report template"], summary="Delete an object")
def delete_image(filename: str,
                 _=Depends(AuthService.check_user_access_token)) -> None:
    ReportTemplateService.delete_image(filename)

################################################# GET ########################################


@core_app.get("/report-template/{id}", tags=["Report template"], summary="Get a report", response_model=None)
def get_by_id(id: str, _=Depends(AuthService.check_user_access_token)) -> ReportTemplateFullDTO:
    return ReportTemplateService.get_by_id_and_check(id).to_full_dto()


@core_app.post("/report-template/search", tags=["Report template"], summary="Advanced search for reports")
def search(search_dict: SearchParams,
           page: Optional[int] = 1,
           number_of_items_per_page: Optional[int] = 20,
           _=Depends(AuthService.check_user_access_token)) -> PageDTO[ReportTemplateDTO]:
    """
    Advanced search on experiment
    """

    return ReportTemplateService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/report-template/search-name/{name}", tags=["Report template"],
              summary="Search for report by name")
def search_by_name(name: str,
                   page: Optional[int] = 1,
                   number_of_items_per_page: Optional[int] = 20,
                   _=Depends(AuthService.check_user_access_token)) -> PageDTO[ReportTemplateDTO]:
    return ReportTemplateService.search_by_name(name, page, number_of_items_per_page).to_dto()
