from fastapi import Depends

from gws_core.scenario.scenario_dto import ScenarioDTO

from ...core_controller import core_app
from ...user.authorization_service import AuthorizationService
from .robot_service import RobotService


@core_app.post(
    "/run/astro-travel-scenario",
    tags=["Astro boy travels"],
    summary="Run the travel scenario of astro",
)
def run_astro_travel_scenario(
    _=Depends(AuthorizationService.check_user_access_token),
) -> ScenarioDTO:
    """
    Run astrobot scenario.
    """

    return RobotService.run_robot_travel().to_dto()


@core_app.post(
    "/run/astro-super-travel-scenario",
    tags=["Astro boy travels"],
    summary="Run supertravel scenario of astros",
)
def run_astro_super_travel_scenario(
    _=Depends(AuthorizationService.check_user_access_token),
) -> ScenarioDTO:
    """
    Run astrobot scenario.
    """

    return RobotService.run_robot_super_travel().to_dto()
