

import os
from typing import Type

from gws_core.config.config_params import ConfigParams
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.impl.file.file import File
from gws_core.impl.plotly.plotly_resource import PlotlyResource
from gws_core.task.converter.exporter import (ResourceExporter,
                                              exporter_decorator)
from gws_core.task.converter.importer import (ResourceImporter,
                                              importer_decorator)


@importer_decorator(unique_name="PlotlyImporter", target_type=PlotlyResource, supported_extensions=['json'],
                    human_name="Plotly resource importer",
                    short_description="Import a json file into a plotly interactive resource")
class PlotlyImporter(ResourceImporter):
    """
    Importer for plotly resources.

    This importer is used to import a json file into a plotly interactive resource.

    This can be useful is a task produce a plotly figure as a json file (like environment agents) and
    you want to import it into a plotly resource.

    This can be use if the json file created by the PlotlyExporter.

    """

    def import_from_path(self, source: File, params: ConfigParams, target_type: Type[PlotlyResource]) -> PlotlyResource:
        if source.is_empty():
            raise BadRequestException(GWSException.EMPTY_FILE.value, unique_code=GWSException.EMPTY_FILE.name,
                                      detail_args={'filename': source.path})

        return PlotlyResource.from_json_file(source.path)


@exporter_decorator(unique_name="PlotlyExporter", source_type=PlotlyResource,
                    human_name="Plotly resource exporter",
                    short_description="Export a plotly interactive resource into a json file")
class PlotlyExporter(ResourceExporter):
    """
    Exporter for plotly resources.

    This exporter is used to export a plotly interactive resource into a json file.

    Then is can be imported from the PlotlyImporter.
    """

    def export_to_path(
            self, source: PlotlyResource, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:

        file_name = params.get_value('file_name', source.name) or 'plotly'
        file_path = os.path.join(dest_dir, file_name + '.json')
        source.export_to_path(file_path)
        return File(file_path)
