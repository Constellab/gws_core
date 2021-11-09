
import os
from typing import Any, Type

from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator


@resource_decorator(unique_name="FsNode", hide=True)
class FSNode(Resource):
    """
    Node class to manage resources that are stored in the server (as file or folder)

    /!\ The class that extend file can only have a path and  file_store_uri attributes. Other attributes will not be
    provided when creating the resource
    """

    path: str = ""
    file_store_uri: str = ""

    def __init__(self, path: str = ""):
        super().__init__()
        self.path = path

    def _exists(self):
        return os.path.exists(self.path)

    @property
    def name(self):
        return ''

    @classmethod
    def get_resource_model_type(cls) -> Type[Any]:
        """Return the resource model associated with this Resource
        //!\\ To overwrite only when you know what you are doing

        :return: [description]
        :rtype: Type[Any]
        """
        from .fs_node_model import FSNodeModel
        return FSNodeModel
