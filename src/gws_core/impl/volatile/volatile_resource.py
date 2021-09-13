# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator

@resource_decorator("VolatileResource", hide=True)
class VolatileResource(Resource):
    """Volatile resource"""
    pass