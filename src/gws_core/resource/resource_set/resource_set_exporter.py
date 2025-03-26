

import os
from typing import Dict, List, Type

from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.core.utils.logger import Logger
from gws_core.impl.file.file import File
from gws_core.impl.file.fs_node import FSNode
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.task.converter.converter_service import ConverterService
from gws_core.task.converter.exporter import (ResourceExporter,
                                              exporter_decorator)
from gws_core.task.task_typing import TaskTyping


@exporter_decorator(unique_name="ResourceSetExporter", source_type=ResourceListBase, human_name="Resource set exporter",
                    short_description="Export a resource set to a zip file")
class ResourceSetExporter(ResourceExporter):
    """ Export a sub resources of a resource set to a zip file

        /!\ If an exporter doesn't exist for a resource type, the resource will be ignored.
        If the exporter of the resource type has some required parameters, the resource will be ignored.
    """

    def export_to_path(
            self, source: ResourceListBase, dest_dir: str, params: ConfigParams, target_type: Type[FSNode]) -> FSNode:

        # use to store the exported files
        fs_nodes: List[FSNode] = []

        # use to store the exporter per typing name locally
        exporters: Dict[str, Type[ResourceExporter]] = {}

        for resource in source.get_resources_as_set():

            # if the resource is a file, add it to the list directly
            if isinstance(resource, FSNode):
                fs_nodes.append(resource)
                continue

            resource_typing_name = resource.get_typing_name()
            if resource_typing_name not in exporters:
                try:
                    exporter_typing: TaskTyping = ConverterService.get_resource_exporter_from_name(
                        resource_typing_name)
                    exporters[resource_typing_name] = exporter_typing.get_type()
                except Exception:
                    Logger.info(
                        f"Can't find exporter for resource {resource_typing_name}")
                    continue

            # store the exporter for the resource type
            exporter: ResourceExporter = exporters[resource_typing_name]

            # skip the exporter if 1 config is not optional
            if not exporter.config_specs.all_config_are_optional():
                Logger.info(
                    f"Skipping exporter {exporter.get_typing_name()} because it has required config")

            # call the exporter without config
            fs_nodes.append(exporter.call(resource, params={}))

        # create a zip file with all the exported files
        temp_dir = self.create_tmp_dir()
        zip_path = os.path.join(temp_dir, f"{source.name or 'export'}.zip")

        zip = ZipCompress(zip_path)

        for file in fs_nodes:
            zip.add_fs_node(file.path, file.get_default_name())

        zip.close()

        return File(zip_path)
