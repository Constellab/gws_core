

import os
from typing import Type

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.utils.compress.tar_compress import TarGzCompress
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.resource.resource import Resource
from gws_core.task.converter.exporter import (ResourceExporter,
                                              exporter_decorator)


@exporter_decorator("FolderExporter", source_type=Folder, human_name="Folder exporter",
                    short_description="Export a folder to a zip or tar.gz file")
class FolderExporter(ResourceExporter):

    config_specs: ConfigSpecs = {
        'compression': StrParam(optional=True,
                                human_name="Compression type",
                                default_value="zip",
                                allowed_values=["zip",  "tar.gz"])
    }

    def export_to_path(self, source: Resource, dest_dir: str, params: ConfigParams, target_type: Type[FSNode]) -> File:

        folder: Folder = source
        tmp_dir = self.create_tmp_dir()
        destination = os.path.join(tmp_dir, FileHelper.get_dir_name(folder.path))

        folder_name = FileHelper.get_dir_name(folder.path)

        compression = params.get_value('compression')
        if compression == "zip":
            destination += folder_name + ".zip"
            self.log_info_message('Compressing folder ' + folder_name + ' to ' + destination)
            ZipCompress.compress_dir(folder.path, destination)
        elif compression == "tar.gz":
            destination += folder_name + ".tar.gz"
            self.log_info_message('Compressing folder ' + folder_name + ' to ' + destination)
            TarGzCompress.compress_dir(folder.path, destination)
        else:
            raise Exception("Compression type not supported")

        return File(destination)
