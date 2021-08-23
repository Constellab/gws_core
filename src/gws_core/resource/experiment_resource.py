from peewee import CharField, IntegerField, ModelSelect

from ..core.model.model import Model
from ..model.typing_manager import TypingManager


class ExperimentResource(Model):
    """
    ExperimentResource class

    This class manages 1-to-many relationships between experiments and child resources (i.e. resources
    generated from related experiments)

    Mapping: [1](Experiment) ---(generate)---> [*](ResourceModel)

    Because resources are allowed to be stored in different tables (e.g. after model inheritance), this class
    allows to load the related resources from the proper tables.
    """

    # Todo:
    # -----
    # * Try to replace `experiment_id` and `resource_id` columns by foreign keys with `lazy_load=False`

    experiment_id = IntegerField(null=False, index=True)
    resource_id = IntegerField(null=False, index=True)
    resource_typing_name = CharField(null=False, index=True)
    _table_name = "gws_experiment_resource"

    @property
    def resource(self):
        """
        Returns the resource
        """
        from .resource_model import ResourceModel
        return ResourceModel.get_by_id(self.resource_id)

    @property
    def experiment(self):
        """
        Returns the experiment
        """

        from ..experiment.experiment import Experiment
        return Experiment.get_by_id(self.experiment_id)

    @classmethod
    def get_by_id_and_tying_name(cls, resource_id: int, typing_name: str) -> ModelSelect:
        return ExperimentResource.get(
            (ExperimentResource.resource_id == resource_id) &
            (ExperimentResource.resource_typing_name == typing_name))

    class Meta:
        indexes = (
            (("experiment_id", "resource_id", "resource_typing_name"), True),
        )
