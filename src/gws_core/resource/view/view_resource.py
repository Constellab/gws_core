# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigParamsDict
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.dict_r_field import DictRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.view.any_view import AnyView
from gws_core.resource.view.view import View
from gws_core.resource.view.view_decorator import view
from gws_core.resource.view.view_runner import ViewRunner


@resource_decorator(unique_name="ViewResource", human_name="View resource",
                    short_description="Resource that contains a view",
                    style=TypingStyle.material_icon("multiline_chart"))
class ViewResource(Resource):
    """Special resource that holds a view
    """

    view_dict: dict = DictRField()

    def __init__(self, view_dict: dict = None) -> None:
        super().__init__()
        self.view_dict = view_dict

    @view(view_type=View, human_name="Show view", default_view=True)
    def default_view(self, params: ConfigParams) -> View:
        return AnyView(self.view_dict)

    @staticmethod
    def from_resource(resource: Resource, view_method_name: str,
                      config_values: ConfigParamsDict = None) -> 'ViewResource':
        view_runner: ViewRunner = ViewRunner(resource, view_method_name, config_values)

        view_runner.generate_view()

        # call the view to dict
        view_dto = view_runner.call_view_to_dto()

        return ViewResource(view_dto.to_json_dict())
