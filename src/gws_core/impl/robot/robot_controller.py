

from fastapi import Depends

from gws_core.experiment.experiment_dto import ExperimentDTO

from ...core_controller import core_app
from ...user.auth_service import AuthService
from .robot_service import RobotService


@core_app.post("/run/astro-travel-experiment", tags=["Astro boy travels"], summary="Run the travel experiment of astro")
def run_astro_travel_experiment(_=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Run astrobot experiment.
    """

    return RobotService.run_robot_travel().to_dto()


@core_app.post("/run/astro-super-travel-experiment", tags=["Astro boy travels"],
               summary="Run supertravel experiment of astros")
def run_astro_super_travel_experiment(_=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    """
    Run astrobot experiment.
    """

    return RobotService.run_robot_super_travel().to_dto()
