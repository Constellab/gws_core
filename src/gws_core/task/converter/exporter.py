import os
import traceback
from abc import abstractmethod
from collections.abc import Callable
from typing import final

from typing_extensions import TypedDict

from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_deprecated import TypingDeprecated
from gws_core.model.typing_style import TypingStyle

from ...brick.brick_service import BrickService
from ...config.config_params import ConfigParams
from ...config.config_specs import ConfigSpecs
from ...core.utils.settings import Settings
from ...core.utils.utils import Utils
from ...impl.file.file import File
from ...impl.file.fs_node import FSNode
from ...resource.resource import Resource
from ...task.task_decorator import task_decorator
from .converter import Converter, decorate_converter

EXPORT_TO_PATH_META_DATA_ATTRIBUTE = "_import_from_path_meta_data"


class ExportToPathMetaData(TypedDict):
    specs: ConfigSpecs
    fs_node_type: type[File]
    inherit_specs: bool


def exporter_decorator(
    unique_name: str,
    source_type: type[Resource],
    target_type: type[File] = File,
    human_name: str | None = None,
    short_description: str | None = None,
    hide: bool = False,
    style: TypingStyle | None = None,
    deprecated: TypingDeprecated | None = None,
) -> Callable:
    """ Decorator to place on a ResourceExporter. It defines a special task to export a resource (of type resource_type) to
    a File (file or folder)
    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param source_type: Type of the resource input for the export
    :type source_type: Type[Resource]
    :param target_type: Type of the file output after the export, leave it to File if you want to export to a basic file
    :type target_type: Type[File], optional
    :param human_name: optional name that will be used in the interface when viewing the tasks.
                        If not defined, an automatic is generated.
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the tasks. Must not be longer than 255 caracters.
                              If not defined, an automatic is generated
    :type short_description: str, optional
    :param hide: Only the task with hide=False will be available in the interface(web platform), other will be hidden.
                It is useful for task that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional
    :param style: style of the task, view TypingStyle object for more info. If not provided, takes the style of source_type resource, defaults to None
    :type style: TypingStyle, optional
    :param deprecated: object to tell that the object is deprecated. See TypingDeprecated for more info, defaults to None
    :type deprecated: TypingDeprecated, optional

    :return: [description]
    :rtype: Callable
    """

    def decorator(task_class: type[ResourceExporter]):
        try:
            if not Utils.issubclass(task_class, ResourceExporter):
                BrickService.log_brick_error(
                    task_class,
                    f"The exporter_decorator is used on the class: {task_class.__name__} and this class is not a sub class of ResourceExporter",
                )
                return task_class

            if not Utils.issubclass(target_type, File):
                BrickService.log_brick_error(
                    task_class,
                    f"Error in the exporter_decorator of class {task_class.__name__}. The target_type must be an File or child class",
                )
                return task_class

            human_name_computed = human_name or source_type.get_human_name() + " exporter"
            short_description_computed = (
                short_description or f"Export {source_type.get_human_name()} to a file"
            )

            # mark the resource as exportable
            source_type.__set_is_exportable__(True)

            # register the task
            decorate_converter(
                task_class=task_class,
                unique_name=unique_name,
                task_type="EXPORTER",
                source_type=source_type,
                target_type=target_type,
                related_resource=source_type,
                human_name=human_name_computed,
                short_description=short_description_computed,
                hide=hide,
                style=style,
                deprecated=deprecated,
            )
        except Exception as err:
            traceback.print_stack()
            BrickService.log_brick_error(task_class, str(err))

        return task_class

    return decorator


@task_decorator("ResourceExporter", hide=True)
class ResourceExporter(Converter):
    """Generic task that take a file as input and return a resource

    Override the export_to_path method to export the resource into a File
    """

    # The output spec can't be overrided, it will be automatically define with the correct resource type
    input_specs = InputSpecs({"source": InputSpec(Resource)})

    # //!\\ The output specs can be overrided, BUT the ResourceExporter task must
    # have 1 output called file that extend File (like File)
    output_specs = OutputSpecs({"target": OutputSpec(File)})

    # Override the config_spec to define custom spec for the exporter
    config_specs = ConfigSpecs({})

    @final
    def convert(self, source: Resource, params: ConfigParams, target_type: type[Resource]) -> File:
        # Create a new temp_dir to create the file here
        temp_dir: str = self.create_tmp_dir()

        result: FSNode
        try:
            result = self.export_to_path(source, temp_dir, params, target_type)
        except Exception as err:
            raise Exception(
                f"Cannot export the resource '{source.name}' using exporter '{self.get_typing_name()}' to a file, error : {err}"
            )

        if not isinstance(result, FSNode):
            raise Exception(
                f"Cannot export the resource '{source.name}' using exporter '{self.get_typing_name()}' to a file, the result is not a FSNode"
            )

        # if the result is a folder, zip it
        if isinstance(result, Folder):
            self.log_info_message(f"Zip the folder {result.path}")
            tmp_dir = Settings.make_temp_dir()
            zip_file = os.path.join(tmp_dir, FileHelper.get_dir_name(result.path) + ".zip")
            ZipCompress.compress_dir(result.path, zip_file)
            return File(zip_file)
        elif isinstance(result, File):
            return result
        else:
            raise Exception(
                f"Cannot export the resource '{source.name}' using exporter '{self.get_typing_name()}' to a file, the result is not a File nor a Folder"
            )

    @abstractmethod
    def export_to_path(
        self, source: Resource, dest_dir: str, params: ConfigParams, target_type: type[FSNode]
    ) -> FSNode:
        """Override this method to generate a fs_node (File or Folder) from the resource. If the result is a folder,
        it will be automatically zipped.

        :param resource: resource to export to fs_node
        :type resource: Type[Resource]
        :param dest_dir: destination directory for the fs_node
        :type dest_dir: str
        :param params: config params for the export
        :type params: ConfigParams
        :param target_type: file type of the result, defined in output_specs. Useful to make generic exporter
        :type params: Type[File]
        :return: resource of type target_type
        :rtype: File
        """
