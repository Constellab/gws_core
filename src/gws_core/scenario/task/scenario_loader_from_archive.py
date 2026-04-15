from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import BoolParam, StrParam
from gws_core.core.service.front_service import FrontService
from gws_core.core.utils.utils import Utils
from gws_core.impl.file.file import File
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_archive_zipper import ScenarioArchiveZipper
from gws_core.scenario.scenario_builder import ScenarioBuilder
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.task.scenario_downloader_base import ScenarioDownloaderCreateOption
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.share.shared_dto import ShareEntityCreateMode
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(
    "ScenarioLoaderFromArchive",
    human_name="Load scenario from archive",
    short_description="Load a scenario and its resources from a single tar archive",
    style=TypingStyle.material_icon("unarchive"),
)
class ScenarioLoaderFromArchive(Task):
    """Load a scenario from a self-contained tar archive file.

    The archive must have been created by the ScenarioArchiveZipperTask (or
    ScenarioArchiveZipper). It contains the full scenario metadata, protocol
    definition, and selected resources bundled as individual tar files.

    This task reconstructs the scenario locally without making any API calls
    to an external lab.

    ## Inputs
    - **archive**: A tar archive file containing the scenario and its resources.

    ## Outputs
    - **scenario**: The loaded scenario.

    ## Parameters
    - **create_option**: How to handle an existing scenario with the same ID.
    - **auto_run**: Automatically run the scenario after loading.
    - **skip_scenario_tags**: Skip importing scenario tags.
    - **skip_resource_tags**: Skip importing resource tags.
    """

    input_specs: InputSpecs = InputSpecs(
        {"archive": InputSpec(File, human_name="Scenario archive")}
    )

    output_specs: OutputSpecs = OutputSpecs(
        {"scenario": OutputSpec(ScenarioResource, human_name="Scenario")}
    )

    config_specs = ConfigSpecs(
        {
            "create_option": StrParam(
                human_name="Create option",
                short_description="This applies for the scenario and the resources",
                allowed_values=Utils.get_literal_values(ScenarioDownloaderCreateOption),
                default_value="Update if exists",
            ),
            "auto_run": BoolParam(
                default_value=False,
                human_name="Run scenario after loading",
                short_description="If true, the scenario will be automatically run after loading",
            ),
            "skip_scenario_tags": BoolParam(
                default_value=False,
                human_name="Skip scenario tags",
                short_description="If true, the scenario tags will not be set",
            ),
            "skip_resource_tags": BoolParam(
                default_value=False,
                human_name="Skip resource tags",
                short_description="If true, the resource tags will not be set",
            ),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        archive_file: File = inputs["archive"]
        create_option: str = params["create_option"]
        auto_run: bool = params["auto_run"]

        self.log_info_message("Extracting scenario archive")

        # Unzip the archive
        archive_package, resource_zip_paths = ScenarioArchiveZipper.unzip(archive_file.path)

        scenario_export = archive_package.scenario_export

        # Resolve create mode
        create_mode: ShareEntityCreateMode = (
            ShareEntityCreateMode.NEW_ID
            if create_option == "Force new scenario"
            else ShareEntityCreateMode.KEEP_ID
        )

        is_update_mode = create_option == "Update if exists"

        # Check for existing scenario in KEEP_ID mode
        if create_mode == ShareEntityCreateMode.KEEP_ID:
            existing = Scenario.get_by_id(scenario_export.scenario.id)
            if existing:
                if is_update_mode:
                    self.log_info_message(
                        f"Scenario '{existing.title}' already exists, will update it"
                    )
                else:
                    raise Exception(
                        "The scenario already exists in the current lab."
                        + f' <a href="{FrontService().get_scenario_url(existing.id)}">Click here to view the existing scenario</a>.'
                    )

        if not scenario_export.protocol.data.graph:
            raise Exception("The scenario protocol graph is missing.")

        self.log_info_message("Building scenario")

        # Build the scenario (Phase 1: transaction - creates shell resources)
        builder = ScenarioBuilder(
            scenario_info=scenario_export,
            origin=archive_package.origin,
            create_mode=create_mode,
            message_dispatcher=self.get_message_dispatcher(),
            skip_resource_tags=params.get_value("skip_resource_tags"),
            skip_scenario_tags=params.get_value("skip_scenario_tags"),
        )

        scenario = builder.build()

        # Phase 2: fill shell resources with content from the archive
        self.log_info_message(f"Loading {len(resource_zip_paths)} resources from archive")
        builder.fill_zip_resources(resource_zip_paths)

        if auto_run:
            self.log_info_message("Auto running the scenario")
            scenario_proxy = ScenarioProxy.from_existing_scenario(scenario.id)
            if scenario_proxy.is_running():
                scenario_proxy.stop_or_remove_from_queue()
            if scenario_proxy.is_finished():
                scenario_proxy.reset_error_processes()
            scenario_proxy.add_to_queue()

        return {"scenario": ScenarioResource(scenario.id)}
