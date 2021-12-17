# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Type, Union

from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.utils.logger import Logger
from gws_core.impl.file.file import File
from gws_core.impl.file.fs_node import FSNode
from gws_core.resource.resource import Resource
from gws_core.task.converter.importer import ResourceImporter
from gws_core.task.task_runner import TaskRunner


# TODO to delete
class ImporterRunner():

    _task_runner: TaskRunner

    def __init__(self, importer_type: Type[ResourceImporter], fs_node: Union[FSNode, str],
                 params: ConfigParamsDict = None) -> None:
        """Object to run a ResourceImporter tasks

          :param importer_type: type of the ResourceImporter to run
          :type importer_type: Type[ResourceImporter]
          :param fs_node: provide a FsNode or a string. If a string, it create a File with the string as path
          :type fs_node: Union[FSNode, str]
         """

        Logger.error('Deprecated, use the ResourceImporter.call_importer() instead')

        fs_node_obj: FSNode
        if isinstance(fs_node, FSNode):
            fs_node_obj = fs_node
        else:
            fs_node_obj = File(fs_node)

        self._task_runner = TaskRunner(importer_type, params=params, inputs={'file': fs_node_obj})

    def run(self) -> Resource:
        # call the run async method in a sync function
        with ThreadPoolExecutor() as e:
            outputs = e.submit(asyncio.run, self._task_runner.run()).result()
            return outputs['resource']
