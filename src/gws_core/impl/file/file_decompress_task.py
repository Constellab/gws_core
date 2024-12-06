

from typing import Literal, Type

from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.utils.compress.compress import Compress
from gws_core.impl.file.folder import Folder
from gws_core.resource.resource_loader import ResourceLoader
from gws_core.share.shared_dto import ShareEntityCreateMode
from gws_core.task.converter.importer import (ResourceImporter,
                                              importer_decorator)

from ...config.config_params import ConfigParams
from ...resource.resource import Resource
from .file import File


@importer_decorator(unique_name="FileDecompressTask", target_type=Resource,
                    human_name="Decompress file",
                    short_description="Decompress a file into a folder or a resource if it's a zipped resource",
                    supported_extensions=list(Compress.get_all_supported_extensions()),
                    output_sub_class=True,
                    style=Folder.copy_style())
class FileDecompressTask(ResourceImporter):

    config_specs: ConfigSpecs = {
        'mode':
        StrParam(
            allowed_values=['Auto', 'Always to folder'],
            default_value='Auto',
            human_name="Mode",
            short_description="'Always to folder' will ignore zipped resource and just decompress file."), }

    resource_loader: ResourceLoader = None

    def import_from_path(self, source: File, params: ConfigParams, target_type: Type[Resource]) -> Resource:

        # case of a file that is not a zip, we directly save it as a resource
        if not Compress.is_compressed_file(source.path):
            raise Exception('The provided file is not a compressed file or is not supported, supported extensions are: ' +
                            ', '.join(Compress.get_all_supported_extensions()))

        mode: Literal['Auto', 'Always to folder'] = params.get_value('mode')

        # Convert the zip file to a resource
        self.log_info_message("Decompressing the file")
        self.resource_loader = ResourceLoader.from_compress_file(source.path, ShareEntityCreateMode.NEW_ID)

        if mode == 'Always to folder':
            return self.resource_loader.load_fs_node_resource()
        else:
            self.log_info_message("Loading the resource")
            return self.resource_loader.load_resource()

    def run_after_task(self) -> None:
        """Save share info, clean temp files, etc
        """
        if not self.resource_loader:
            return

        # clear temps files
        self.log_info_message("Cleaning the temp files")
        self.resource_loader.delete_resource_folder()
