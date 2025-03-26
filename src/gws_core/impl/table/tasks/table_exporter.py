

import os
from typing import Type

from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper

from ....config.config_params import ConfigParams
from ....config.config_specs import ConfigSpecs
from ....config.param.param_spec import BoolParam, StrParam
from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....task.converter.exporter import ResourceExporter, exporter_decorator
from ..table import Table


@exporter_decorator(unique_name="TableExporter", source_type=Table)
class TableExporter(ResourceExporter):
    config_specs = ConfigSpecs({
        'file_name': StrParam(optional=True, human_name="File name", short_description="File name (without extension)"),
        'file_format': StrParam(optional=True, default_value=Table.DEFAULT_FILE_FORMAT, allowed_values=Table.ALLOWED_FILE_FORMATS, human_name="File format"),
        'delimiter': StrParam(allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER, human_name="Delimiter character", short_description="Only for CSV files"),
        # 'write_metadata': BoolParam(default_value=True, short_description="Set True to write metadata"),
        'write_header': BoolParam(default_value=True, visibility=BoolParam.PROTECTED_VISIBILITY, human_name="Write header", short_description="Set True to write column names (header), False otherwise"),
        'write_index': BoolParam(default_value=False, visibility=BoolParam.PROTECTED_VISIBILITY, human_name="Write index", short_description="Set True to write row names (index), False otherwise"),
    })

    def export_to_path(self, source: Table, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        file_name = params.get_value('file_name', source.name) or 'table'
        file_format = FileHelper.clean_extension(params.get_value('file_format', Table.DEFAULT_FILE_FORMAT))
        file_path = os.path.join(dest_dir, file_name + '.' + file_format)
        sep = params.get_value('delimiter', Table.DEFAULT_DELIMITER)
        if sep == "tab":
            sep = "\t"
        elif sep == "space":
            sep = " "
        elif sep == "auto":
            sep = ","

        if file_format in Table.ALLOWED_XLS_FILE_FORMATS:
            source.get_data().to_excel(file_path)
        elif file_format in Table.ALLOWED_TXT_FILE_FORMATS:
            source.get_data().to_csv(
                file_path,
                sep=sep,
                header=params.get_value('write_header'),
                index=params.get_value('write_index'),
                index_label="index"
            )

            comments = source.comments
            # if params.get_value('write_metadata', True):
            #     tags = source.get_meta()
            #     if comments:
            #         comments += "\n#" + json.dumps(tags)
            #     else:
            #         comments +q= "#" + json.dumps(tags)
            with open(file_path, 'r+', encoding="utf-8") as fp:
                content = fp.read()
                fp.seek(0, 0)
                if comments:
                    fp.write(comments.strip() + '\n' + content)
        else:
            raise BadRequestException(
                f"Valid file formats are {Table.ALLOWED_FILE_FORMATS}.")

        return target_type(path=file_path)
