
from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.folder.space_folder_dto import ExternalSpaceFolder, ExternalSpaceFolders
from gws_core.folder.space_folder_service import SpaceFolderService
from gws_core.lab.dev_env_service import DevEnvService
from gws_core.lab.system_dto import SettingsDTO
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.shared_dto import GenerateUserAccessTokenForSpaceResponse
from gws_core.space.space_dto import LabActivityReponseDTO, SpaceSyncObjectDTO
from gws_core.space.space_object_service import SpaceObjectService
from gws_core.user.activity.activity_service import ActivityService
from gws_core.user.authentication_service import AuthenticationService

from ..core.exception.exception_handler import ExceptionHandler
from ..core.service.settings_service import SettingsService
from ..user.user_dto import UserFullDTO, UserLoginInfo
from ..user.user_service import UserService
from ._auth_space import AuthSpace

space_app = FastAPI(docs_url="/docs")


# Catch HTTP Exceptions
@space_app.exception_handler(HTTPException)
async def all_http_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)


# Catch RequestValidationError (422 Unprocessable Entity)


@space_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return ExceptionHandler.handle_request_validation_error(exc)


# Catch all other exceptions
@space_app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)


##################################################### GLOBAL  #####################################################
@space_app.get("/settings", summary="Get settings")
def get_settings(_=Depends(AuthSpace.check_space_api_key)) -> SettingsDTO:
    return SettingsService.get_settings().to_dto()


@space_app.get("/health-check", summary="Health check route")
def health_check() -> bool:
    """
    Simple health check route
    """

    return True


##################################################### USER #####################################################


class TokenData(BaseModelDTO):
    access_token: str
    token_type: str


class UserIdData(BaseModelDTO):
    id: str


@space_app.post("/user/generate-temp-access", tags=["User management"])
def generate_user_temp_access(
    user_login_info: UserLoginInfo, _=Depends(AuthSpace.check_space_api_key_and_user)
) -> dict:
    """
    Generate a temporary link for the user to login in the lab
    """

    return {"temp_token": AuthenticationService.generate_user_temp_access(user_login_info)}


@space_app.put("/user/{id_}/activate", tags=["User management"])
def activate_user(id_: str, _=Depends(AuthSpace.check_space_api_key_and_user)) -> UserFullDTO:
    """
    Activate a user. Requires space privilege.

    - **id_**: the user id_
    """

    return UserService.activate_user(id_).to_full_dto()


@space_app.put("/user/{id_}/deactivate", tags=["User management"])
def deactivate_user(id_: str, _=Depends(AuthSpace.check_space_api_key_and_user)) -> UserFullDTO:
    """
    Deactivate a user. Require space privilege.

    - **id_**: the user id_
    """

    return UserService.deactivate_user(id_).to_full_dto()


@space_app.get("/user/{id_}", tags=["User management"])
def get_user(id_: str, _=Depends(AuthSpace.check_space_api_key_and_user)) -> UserFullDTO:
    """
    Get the details of a user. Require space privilege.

    - **id_**: the user id_
    """

    return UserService.get_user_by_id(id_).to_full_dto()


@space_app.post("/user", tags=["User management"])
def create_user(user: UserFullDTO, _=Depends(AuthSpace.check_space_api_key)) -> UserFullDTO:
    """
    Create a new user.
    """

    return UserService.create_or_update_user_dto(user).to_full_dto()


@space_app.get("/user", tags=["User management"])
def get_users(_=Depends(AuthSpace.check_space_api_key_and_user)) -> list[UserFullDTO]:
    """
    Get the all the users. Require space privilege.
    """
    users = UserService.get_all_users()
    return [user.to_full_dto() for user in users]


##################################################### FOLDER #####################################################
@space_app.post("/folder", tags=["Folder"])
def sync_folder(folder: ExternalSpaceFolder, _=Depends(AuthSpace.check_space_api_key)) -> None:
    """
    Register a space folder to the lab
    """

    SpaceFolderService.synchronize_space_folder(folder)


@space_app.delete("/folder/{id_}", tags=["Folder"])
def delete_folder(id_: str, _=Depends(AuthSpace.check_space_api_key)) -> None:
    """
    Remove a folder from the lab
    """

    SpaceFolderService.delete_folder(id_)


@space_app.post("/folder/sync", tags=["Folder"])
def sync_all_folders(
    folders: ExternalSpaceFolders, _=Depends(AuthSpace.check_space_api_key)
) -> None:
    """
    Sync all the folders from the space to the lab
    """

    SpaceFolderService.synchronize_all_folders(folders)


@space_app.put("/folder/{id_}/move/{parent_id}", tags=["Folder"])
def move_folder(id_: str, parent_id: str, _=Depends(AuthSpace.check_space_api_key)) -> None:
    """
    Move a folder to another folder
    """

    SpaceFolderService.move_folder(id_, parent_id)


############################################### SCENARIO #####################################################


@space_app.get("/lab/global-activity", tags=["Scenario"])
def lab_activity(_=Depends(AuthSpace.check_space_api_key)) -> LabActivityReponseDTO:
    """
    Count the number of running or queued scenarios

    """

    last_activity = ActivityService.get_last_activity()

    return LabActivityReponseDTO(
        running_scenarios=ScenarioService.count_running_or_queued_scenarios(),
        queued_scenarios=ScenarioService.count_queued_scenarios(),
        last_activity=last_activity.to_dto() if last_activity is not None else None,
        dev_env_running=DevEnvService.dev_env_is_running(),
    )


@space_app.put("/scenario/sync", tags=["Scenario"])
def sync_scenarios(scenario: SpaceSyncObjectDTO, _=Depends(AuthSpace.check_space_api_key)) -> None:
    """
    Sync all the scenarios from the space to the lab
    """

    SpaceObjectService.sync_scenario_from_space(scenario)


############################################### NOTE #####################################################


@space_app.put("/note/sync", tags=["Note"])
def sync_notes(note: SpaceSyncObjectDTO, _=Depends(AuthSpace.check_space_api_key)) -> None:
    """
    Sync all the notes from the space to the lab
    """

    SpaceObjectService.sync_note_from_space(note)


############################################### SHARE #####################################################


@space_app.post("/share/{token}/generate-user-access-token", tags=["Share"])
def generate_user_access_token(
    token: str, user: UserFullDTO, _=Depends(AuthSpace.check_space_api_key)
) -> GenerateUserAccessTokenForSpaceResponse:
    """
    Route to generate a user access token for a space share link.
    This token usure that the user is connected and has access to the share link.
    """

    return ShareLinkService.generate_user_access_token_for_space_link(token, user)
