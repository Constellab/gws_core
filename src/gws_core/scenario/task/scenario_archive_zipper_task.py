from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.utils.utils import Utils
from gws_core.impl.file.file import File
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.scenario.scenario_archive_zipper import ScenarioArchiveZipper
from gws_core.scenario.task.scenario_downloader_base import ScenarioDownloaderResourceMode
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.user.current_user_service import CurrentUserService


@task_decorator(
    "ScenarioArchiveZipperTask",
    human_name="Export scenario to archive",
    short_description="Export a scenario and its resources into a single tar archive",
    style=TypingStyle.material_icon("archive"),
)
class ScenarioArchiveZipperTask(Task):
    """Export a scenario and its selected resources into a single tar archive file.

    The archive contains the full scenario metadata (protocol, tasks, configuration)
    and the selected resources as individual tar files. This archive is self-contained
    and can be stored externally (e.g., on S3) and later imported using the
    ScenarioLoaderFromArchive task.

    ## Inputs
    - **scenario**: The scenario to export.

    ## Outputs
    - **archive**: A tar file containing the scenario and its resources.

    ## Parameters
    - **resource_mode**: Controls which resources are included in the archive.
    """

    input_specs: InputSpecs = InputSpecs(
        {"scenario": InputSpec(ScenarioResource, human_name="Scenario to export")}
    )

    output_specs: OutputSpecs = OutputSpecs(
        {"archive": OutputSpec(File, human_name="Scenario archive")}
    )

    config_specs = ConfigSpecs(
        {
            "resource_mode": StrParam(
                human_name="Resource mode",
                short_description="Which resources to include in the archive",
                allowed_values=Utils.get_literal_values(ScenarioDownloaderResourceMode),
                default_value="Auto",
            ),
            "compress_format": StrParam(
                human_name="Archive format",
                short_description=(
                    "Archive format to use. Compressed formats (tar.gz, zip) may take a "
                    "long time if the scenario contains big resources."
                ),
                allowed_values=sorted(ScenarioArchiveZipper.COMPRESS_FORMATS.keys()),
                default_value="tar",
            ),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        scenario_resource: ScenarioResource = inputs["scenario"]
        resource_mode: str = params["resource_mode"]
        compress_format: str = params["compress_format"]
        user = CurrentUserService.get_and_check_current_user()

        self.log_info_message(f"Exporting scenario '{scenario_resource.scenario_id}' to archive")

        zipper = ScenarioArchiveZipper(
            scenario_resource.scenario_id, resource_mode, user, compress_format
        )
        archive_path = zipper.zip()

        self.log_info_message("Scenario archive created successfully")

        return {"archive": File(archive_path)}
