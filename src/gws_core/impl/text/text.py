# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.r_field import RField
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from .view.text_view import TextView

# @resource_decorator("Text")
# class Text(Resource):
#     DEFAULT_FILE_FORMAT = "txt"
#     _data: str = RField()

#     def __init__(self, data: str = None):
#         super().__init__()
#         self._set_data(data)

#     def _set_data(self, data: str) -> 'Text':
#         if data is None:
#             data = ""
#         if not isinstance(data, str):
#             raise BadRequestException(
#                 "The data must be a string")
#         self._data = data
#         return self

#     def get_data(self):
#         return self._data

#     @view(view_type=TextView, human_name='Text', short_description='View as text',
#           specs={}, default_view=True)
#     def view_as_text(self, params: ConfigParams) -> TextView:
#         """
#         View as table
#         """

#         return TextView(self._data)
