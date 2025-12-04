from gws_core.core.utils.utils import Utils
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.view.any_view import AnyView
from gws_core.resource.view.view import View

from ...config.config_params import ConfigParams
from ...core.exception.exceptions.bad_request_exception import BadRequestException
from ...resource.r_field.dict_r_field import DictRField
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view.view_decorator import view
from .json_view import JSONView


@resource_decorator(
    "JSONDict",
    human_name="JSON Dict",
    short_description="Resource that holds a JSON dict",
    style=TypingStyle.material_icon("data_object", background_color="#f6995c"),
)
class JSONDict(Resource):
    data: dict = DictRField()

    def __init__(self, data: dict = None):
        super().__init__()
        if data is None:
            data = {}
        else:
            if not isinstance(data, dict):
                raise BadRequestException("The data must be an instance of dict")
        self.data = data

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __setitem__(self, key, val):
        self.data[key] = val

    def __str__(self):
        return super().__str__() + "\n" + "Dictionnary:\n" + self.data.__str__()

    def get_data(self) -> dict:
        return self.data

    def equals(self, other: object) -> bool:
        if not isinstance(other, JSONDict):
            return False

        return Utils.json_are_equals(self.data, other.data)

    @view(
        view_type=View,
        human_name="Default view",
        short_description="View the file content",
        default_view=True,
    )
    def default_view(self, _: ConfigParams) -> View:
        # If the json, is a json of a view
        if View.json_is_from_view(self.data):
            return AnyView(self.data)
        return JSONView(self.data)
