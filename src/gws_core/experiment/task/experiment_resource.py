

from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.service.front_service import FrontService
from gws_core.experiment.experiment import Experiment
from gws_core.impl.json.json_view import JSONView
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.view.view_decorator import view


@resource_decorator("ExperimentResource", human_name="Experiment resource", short_description="Experiment resource",
                    style=TypingStyle.material_icon("experiment", background_color="#735f32"))
class ExperimentResource(Resource):
    """Resource to reference an experiment.

    :param Resource: _description_
    :type Resource: _type_
    :return: _description_
    :rtype: _type_
    """

    experiment_id: str = StrRField()

    experiment: Experiment = None

    def __init__(self, experiment_id: str = None):
        super().__init__()
        self.experiment_id = experiment_id

    def get_experiment(self) -> Experiment:
        if self.experiment is None:
            self.experiment = Experiment.get_by_id_and_check(self.experiment)
        return self.experiment

    @view(view_type=JSONView, human_name="View experiment info", default_view=True)
    def view_experiment(self, config: ConfigParamsDict = None) -> JSONView:
        return JSONView({
            'id': self.experiment_id,
            'title': self.get_experiment().title,
            'url': FrontService.get_experiment_url(self.experiment_id),
        })
