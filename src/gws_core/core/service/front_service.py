# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.utils.settings import Settings


class FrontService():

    @staticmethod
    def get_experiment_url(experiment_id: str) -> str:
        return FrontService.get_app_url() + '/biox/experiment/' + experiment_id

    @staticmethod
    def get_report_url(report_id: str) -> str:
        return FrontService.get_app_url() + '/biox/report/' + report_id

    @staticmethod
    def get_resource_url(resource_id: str) -> str:
        return FrontService.get_app_url() + '/databox/resource/' + resource_id

    @staticmethod
    def get_auto_login_url(expires_in: int) -> str:
        return Settings.get_front_url() + '/auto-login?expiresIn=' + str(expires_in)

    @staticmethod
    def get_app_url() -> str:
        return Settings.get_front_url() + '/app'

    @staticmethod
    def get_front_url() -> str:
        return Settings.get_front_url()
