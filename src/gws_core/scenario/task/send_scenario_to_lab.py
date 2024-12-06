

from datetime import timedelta

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import IntParam
from gws_core.core.utils.date_helper import DateHelper
from gws_core.credentials.credentials_param import CredentialsParam
from gws_core.credentials.credentials_type import (CredentialsDataLab,
                                                   CredentialsType)
from gws_core.external_lab.external_lab_api_service import \
    ExternalLabApiService
from gws_core.external_lab.external_lab_dto import ExternalLabImportRequestDTO
from gws_core.io.io_spec import InputSpec
from gws_core.io.io_specs import InputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.scenario.task.scenario_downloader import ScenarioDownloader
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.share.share_link_service import ShareLinkService
from gws_core.share.shared_dto import GenerateShareLinkDTO, ShareLinkType
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(unique_name="SendScenarioToLab", human_name="Send a scenario to a lab",
                short_description="Send a scenario to another lab using a share link",
                style=TypingStyle.material_icon("cloud_upload"))
class SendScenarioToLab(Task):
    """
    Task to send a scenario to another lab using a share link.

    This task creates a share link for the scenario.

    Then it call the external lab API to import the scenario in the external lab using the share link.

    A credentials of type lab are required in both labs to be able to send and receive scenarios. It
    needs to be the same api_key in both labs.

    """

    input_specs = InputSpecs({'scenario': InputSpec(ScenarioResource, human_name="Scenario to send",
                             short_description="Scenario to send, it must not be running"),
                              })

    config_specs: ConfigSpecs = {
        'credentials': CredentialsParam(credentials_type=CredentialsType.LAB, human_name="Lab credentials",
                                        short_description="The credentials must exist in destination lab"),
        'link_duration': IntParam(human_name='Share link duration in days',
                                  short_description="The share link is not created if a share link already exists for the resource",
                                  min_value=1,
                                  max_value=365, default_value=1),
    }

    INPUT_NAME = 'scenario'

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        current_day = DateHelper.now_utc()

        scenario_resource: ScenarioResource = inputs['scenario']

        scenario = scenario_resource.get_scenario()

        if scenario.is_running:
            raise ValueError("The scenario is running, it cannot be sent to the lab")

        generate_share_link = GenerateShareLinkDTO(
            entity_id=scenario.id,
            entity_type=ShareLinkType.SCENARIO,
            valid_until=current_day + timedelta(days=params.get_value('link_duration'))
        )

        self.log_info_message("Generate share link for the scenario if not exists")
        share_link = ShareLinkService.get_or_create_valid_share_link(generate_share_link)

        # Call the external lab API to import the current scenario
        self.log_info_message("Send the scenario to the lab")
        request_dto = ExternalLabImportRequestDTO(
            # convert to ScenarioDownloader config because ScenarioDownloader is used to download the scenario
            params=ScenarioDownloader.build_config(share_link.get_download_link(), 'Outputs only', 'Skip if exists'),
        )
        credentials: CredentialsDataLab = params.get_value('credentials')

        response = ExternalLabApiService.send_scenario_to_lab(request_dto, credentials,
                                                              CurrentUserService.get_and_check_current_user().id)

        self.log_success_message(f"Scenario sent to the lab, available at {response.scenario_url}")

        return {}
