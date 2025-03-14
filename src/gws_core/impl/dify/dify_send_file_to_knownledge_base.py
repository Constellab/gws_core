from typing import List

from gws_core import (ConfigParams, InputSpec, OutputSpecs, Task, TaskInputs,
                      TaskOutputs, task_decorator)
from gws_core.config.param.param_spec import IntParam, StrParam
from gws_core.core.utils.utils import Utils
from gws_core.credentials.credentials_param import CredentialsParam
from gws_core.credentials.credentials_type import (CredentialsDataOther,
                                                   CredentialsType)
from gws_core.impl.dify.dify_service import (DifyIndexingTechnique,
                                             DifySendDocumentOptions,
                                             DifyService)
from gws_core.impl.file.file import File
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.io.dynamic_io import DynamicInputs
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_set.resource_list import ResourceList


@task_decorator("DifySendFileToKnownledgeBase", human_name="Send files to Dify Knowledge Base",
                short_description="Send as many files or folders as you want to Dify Knowledge Base",
                style=TypingStyle.community_image("dify", "#ffffff"))
class DifySendFileToKnownledgeBase(Task):
    """
    Send as many files or folders as you want to Dify Knowledge Base.

    A dify api key and a dify dataset id are required to send files to the Dify Knowledge Base.
    """

    input_specs = DynamicInputs(
        additionnal_port_spec=InputSpec(FSNode, human_name="Files or folders",
                                        short_description="Files or folders to send to Dify Knowledge Base"),
    )
    output_specs = OutputSpecs()

    config_specs = {
        'api_key': CredentialsParam(credentials_type=CredentialsType.OTHER,
                                    human_name="Dify API Key",
                                    short_description="A credentials that contains 'route' and 'api_key'",
                                    ),
        'dataset_id': StrParam(human_name="Dify knowledge base id",
                               short_description="Id of the Dify knowledge base where to send the files",
                               ),
        'indexing_technique': StrParam(human_name="Indexing technique",
                                       short_description="Indexing technique to use",
                                       allowed_values=Utils.get_literal_values(DifyIndexingTechnique),
                                       default_value='high_quality'),
        'chunk_separator': StrParam(human_name="Chunk separator",
                                    short_description="Separator to use to split the text into chunks",
                                    default_value='\\n\\n'),
        'chunk_max_tokens': IntParam(human_name="Chunk max tokens",
                                     short_description="Max tokens per chunk",
                                     default_value=500, min_value=1),
        'lang': StrParam(human_name="Language",
                         short_description="Language of the document",
                         default_value='en')
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        fs_nodes: ResourceList = inputs[DynamicInputs.SPEC_NAME]

        credentials: CredentialsDataOther = params.get_value('api_key')
        dify_service = DifyService.from_credentials(credentials)

        file_paths: List[str] = []

        for fs_node in fs_nodes.get_resources():
            if isinstance(fs_node, File):
                file_paths.append(fs_node.path)
            elif isinstance(fs_node, Folder):
                files = fs_node.list_all_file_paths()
                file_paths.extend(files)
            else:
                self.log_error_message(f"Resource {fs_node.name} is not a file or a folder")

        options = DifySendDocumentOptions(
            indexing_technique=params.get_value('indexing_technique'),
            chunk_separator=params.get_value('chunk_separator'),
            chunk_max_tokens=params.get_value('chunk_max_tokens'),
            lang=params.get_value('lang')
        )
        progress = 0
        for file_path in file_paths:
            dify_service.send_document(file_path,
                                       params.get_value('dataset_id'),
                                       options)

            progress += 1
            self.update_progress_value(progress / len(file_paths) * 100,
                                       f"File {file_path} sent")

        return {}
