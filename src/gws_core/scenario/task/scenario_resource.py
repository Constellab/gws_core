

from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.service.front_service import FrontService
from gws_core.impl.json.json_view import JSONView
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.view.view_decorator import view
from gws_core.scenario.scenario import Scenario


@resource_decorator("ScenarioResource", human_name="Scenario resource", short_description="Scenario resource",
                    style=TypingStyle.material_icon("scenario", background_color="#735f32"))
class ScenarioResource(Resource):
    """Resource to reference an scenario.

    :param Resource: _description_
    :type Resource: _type_
    :return: _description_
    :rtype: _type_
    """

    scenario_id: str = StrRField()

    scenario: Scenario = None

    def __init__(self, scenario_id: str = None):
        super().__init__()
        self.scenario_id = scenario_id

    def get_scenario(self) -> Scenario:
        if self.scenario is None:
            self.scenario = Scenario.get_by_id_and_check(self.scenario_id)
        return self.scenario

    @view(view_type=JSONView, human_name="View scenario info", default_view=True)
    def view_scenario(self, config: ConfigParamsDict = None) -> JSONView:
        return JSONView({
            'id': self.scenario_id,
            'title': self.get_scenario().title,
            'url': FrontService.get_scenario_url(self.scenario_id),
        })
