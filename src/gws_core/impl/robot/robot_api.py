# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import Depends

from ...core_app import core_app
from ...experiment.experiment import Experiment
from ...user.auth_service import AuthService
from .robot_service import RobotService


@core_app.post("/run/astro-travel-experiment", tags=["Astro boy travels"], summary="Run the travel experiment of astro")
def run_astro_travel_experiment(_=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Run astrobot experiment.
    """

    experiment: Experiment = RobotService.run_robot_travel()
    return experiment.to_json()


@core_app.post("/run/astro-super-travel-experiment", tags=["Astro boy travels"],
               summary="Run supertravel experiment of astros")
def run_astro_super_travel_experiment(_=Depends(AuthService.check_user_access_token)) -> dict:
    """
    Run astrobot experiment.
    """

    experiment: Experiment = RobotService.run_robot_super_travel()
    return experiment.to_json()
