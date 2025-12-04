from gws_core.config.config_params import ConfigParams, ConfigParamsDict
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.dict_r_field import DictRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.view.any_view import AnyView
from gws_core.resource.view.view import View
from gws_core.resource.view.view_decorator import view
from gws_core.resource.view.view_dto import ViewDTO
from gws_core.resource.view.view_runner import ViewRunner


@resource_decorator(
    unique_name="ViewResource",
    human_name="View resource",
    short_description="Resource that contains a view",
    style=TypingStyle.material_icon("multiline_chart", background_color="#496989"),
)
class ViewResource(Resource):
    """Special resource that holds a view"""

    view_dict: dict = DictRField()

    def __init__(self, view_dict: dict = None) -> None:
        """Create the view resource from the view dict

        :param view_dict: dict of a view, defaults to None
        :type view_dict: dict, optional
        """
        super().__init__()
        self.view_dict = view_dict

    @view(view_type=View, human_name="Show view", default_view=True)
    def default_view(self, params: ConfigParams) -> View:
        return AnyView(self.view_dict)

    @staticmethod
    def from_resource(
        resource: Resource, view_method_name: str, config_values: ConfigParamsDict = None
    ) -> "ViewResource":
        """Create a view resource from a resource and a view method name

        :param resource: resource to call the view method on
        :type resource: Resource
        :param view_method_name: name of the view method to call
        :type view_method_name: str
        :param config_values: config value to use on call, defaults to None
        :type config_values: ConfigParamsDict, optional
        :return: _description_
        :rtype: ViewResource
        """
        view_runner: ViewRunner = ViewRunner(resource, view_method_name, config_values)

        view_runner.generate_view()

        # call the view to dict
        view_dto = view_runner.call_view_to_dto()

        return ViewResource(view_dto.to_json_dict())

    @staticmethod
    def from_view(view_: View, view_config_values: ConfigParamsDict = None) -> "ViewResource":
        """Create a view resource directly from the view object

        :param view_: view object to use
        :type view_: View
        :param view_config_values: config value of the view when call to_json_dict, defaults to None
        :type view_config_values: ConfigParamsDict, optional
        :return: _description_
        :rtype: ViewResource
        """
        if not isinstance(view_, View):
            raise Exception("The view object must be an instance of View")

        # create a new config for the view to_dict method based on view specs
        config_params: ConfigParams = view_.get_specs().build_config_params(
            dict(view_config_values or {})
        )
        # disable the pagination of the view because it contains only the data of 1 page
        view_.disable_pagination()
        return ViewResource.from_view_dto(view_.to_dto(config_params))

    @staticmethod
    def from_view_dto(
        view_dto: ViewDTO,
    ) -> "ViewResource":
        """Create a view resource directly from the view dto object

        :param view_: view object to use
        :type view_: View
        :param view_config_values: config value of the view when call to_json_dict, defaults to None
        :type view_config_values: ConfigParamsDict, optional
        :return: _description_
        :rtype: ViewResource
        """
        return ViewResource(view_dto.to_json_dict())
