# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from typing import TYPE_CHECKING, Any, List, Union

from gws_core.config.config_types import ConfigParams
from gws_core.impl.file.file_helper import FileHelper
from gws_core.resource.view import View
from gws_core.resource.view_types import ViewType

if TYPE_CHECKING:
    from gws_core.impl.file.fs_node_model import FSNodeModel


class LocalFolderView(View):
    """
     Class json view.

     The view model is:
     ```
     {
         "type": "folder-view"
         "data": {
           "path": strn
           "content": {
             "name": str,
             "children": [...]
           }
         }
     }
     ```
     """

    _path: str
    _type: ViewType = ViewType.FOLDER

    def __init__(self, dir_path: str):
        super().__init__()
        self._path = dir_path

    def data_to_dict(self, params: ConfigParams) -> dict:
        from gws_core.impl.file.fs_node_model import FSNodeModel
        nodes_models = FSNodeModel.path_start_with(self._path)

        return {
            "path": self._path,
            "content": self._get_content(self._path, nodes_models)
        }

    def _get_content(self, path: str, node_models: List['FSNodeModel']) -> Union[dict, list]:

        _json = {}
        if FileHelper.is_file(path):
            _json['name'] = FileHelper.get_name_with_extension(path)
        else:
            _json['name'] = FileHelper.get_dir_name(path)

        # check if a symbolic resource was already created for this path
        node_model = [x for x in node_models if x.path == path]
        if node_model:
            _json['resource_model_id'] = node_model[0].get_resource_model().id

        # recursive call on folder content
        if FileHelper.is_dir(path):
            children: List[str] = os.listdir(path)
            _json['children'] = []

            for child in children:
                _json['children'].append(self._get_content(os.path.join(path, child), node_models))

        return _json
