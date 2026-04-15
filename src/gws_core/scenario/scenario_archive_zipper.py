import json
import os

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.compress.tar_compress import TarCompress
from gws_core.core.utils.settings import Settings
from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.resource.resource_zipper import ResourceZipper
from gws_core.scenario.scenario_zipper import ScenarioExportPackage
from gws_core.user.user import User


class ScenarioArchivePackage(BaseModelDTO):
    """Metadata stored in scenario_info.json inside the scenario archive."""

    archive_version: int = 1
    scenario_export: ScenarioExportPackage
    origin: ExternalLabWithUserInfo


class ScenarioArchiveZipper:
    """Creates a single tar archive containing a scenario and its selected resources.

    Archive format::

        scenario_archive.tar
        ├── scenario_info.json          # ScenarioArchivePackage
        └── resources/
            ├── <resource_id_1>.tar     # Individual resource tar (ResourceZipper format)
            ├── <resource_id_2>.tar
            └── ...
    """

    ARCHIVE_FILE_NAME = "scenario_archive.tar"
    INFO_JSON_FILE_NAME = "scenario_info.json"
    RESOURCES_DIR_NAME = "resources"
    ARCHIVE_VERSION = 1

    def __init__(self, scenario_id: str, resource_mode: str, user: User):
        self._scenario_id = scenario_id
        self._resource_mode = resource_mode
        self._user = user

    def zip(self) -> str:
        """Export the scenario and selected resources into a single tar archive.

        :return: Path to the generated archive file.
        """
        # Lazy imports to avoid circular dependencies
        from gws_core.scenario.scenario_service import ScenarioService
        from gws_core.scenario.task.scenario_downloader_base import ScenarioDownloaderBase

        scenario_export = ScenarioService.export_scenario(self._scenario_id)

        # Resolve resource mode
        resource_mode = self._resource_mode
        if resource_mode == "Auto":
            resource_mode = ScenarioDownloaderBase.resolve_auto_resource_mode(
                scenario_export.scenario.status, auto_run=False
            )

        # Get the resource IDs to include
        resource_ids: set[str] = set()
        if scenario_export.protocol.data.graph:
            resource_ids = ScenarioDownloaderBase.get_resource_ids_for_mode(
                scenario_export.protocol.data.graph, resource_mode
            )

        # Build origin info
        origin = ExternalLabApiService.get_current_lab_info(self._user)

        # Create temp directory for the archive
        temp_dir = Settings.get_instance().make_temp_dir()
        resources_dir = os.path.join(temp_dir, self.RESOURCES_DIR_NAME)
        os.makedirs(resources_dir)

        # Zip each resource individually using ResourceZipper
        for resource_id in resource_ids:
            resource_zipper = ResourceZipper(self._user)
            resource_zipper.add_resource_model(resource_id)
            resource_tar_path = resource_zipper.close_zip()

            # Move the resource tar into resources/ with the resource ID as filename
            dest_path = os.path.join(resources_dir, f"{resource_id}.tar")
            os.rename(resource_tar_path, dest_path)

        # Write scenario_info.json
        archive_package = ScenarioArchivePackage(
            archive_version=self.ARCHIVE_VERSION,
            scenario_export=scenario_export,
            origin=origin,
        )
        info_json_path = os.path.join(temp_dir, self.INFO_JSON_FILE_NAME)
        with open(info_json_path, "w", encoding="UTF-8") as f:
            json.dump(archive_package.to_json_dict(), f)

        # Create the outer tar archive
        archive_path = os.path.join(temp_dir, self.ARCHIVE_FILE_NAME)
        tar = TarCompress(archive_path)
        tar.add_file(info_json_path, file_name=self.INFO_JSON_FILE_NAME)
        tar.add_dir(resources_dir, dir_name=self.RESOURCES_DIR_NAME)
        tar.close()

        return archive_path

    @classmethod
    def unzip(cls, archive_path: str) -> tuple["ScenarioArchivePackage", dict[str, str]]:
        """Extract a scenario archive and return its metadata and resource tar paths.

        :param archive_path: Path to the scenario archive tar file.
        :return: Tuple of (ScenarioArchivePackage, dict mapping resource_id to tar path).
        """
        temp_dir = Settings.get_instance().make_temp_dir()
        TarCompress.decompress(archive_path, temp_dir)

        # Read and validate scenario_info.json
        info_json_path = os.path.join(temp_dir, cls.INFO_JSON_FILE_NAME)
        if not os.path.exists(info_json_path):
            raise Exception(f"Invalid scenario archive: missing '{cls.INFO_JSON_FILE_NAME}'")

        with open(info_json_path, encoding="UTF-8") as f:
            info_data = json.load(f)

        archive_package = ScenarioArchivePackage.from_json(info_data)

        if archive_package.archive_version != cls.ARCHIVE_VERSION:
            raise Exception(
                f"Unsupported archive version: {archive_package.archive_version}. "
                f"Expected: {cls.ARCHIVE_VERSION}"
            )

        # Scan resources/ folder to build the resource paths dict
        resource_zip_paths: dict[str, str] = {}
        resources_dir = os.path.join(temp_dir, cls.RESOURCES_DIR_NAME)
        if os.path.isdir(resources_dir):
            for filename in os.listdir(resources_dir):
                if filename.endswith(".tar"):
                    resource_id = filename[:-4]  # strip .tar
                    resource_zip_paths[resource_id] = os.path.join(resources_dir, filename)

        return archive_package, resource_zip_paths
