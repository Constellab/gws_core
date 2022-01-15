# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...resource.resource_decorator import resource_decorator
from ..file.file import File


@resource_decorator("JSONFile")
class JSONFile(File):
    """Specific file to .json. This file contains the sames view as the JSONDict resource.

    :param File: [description]
    :type File: [type]
    :return: [description]
    :rtype: [type]
    """

    pass
