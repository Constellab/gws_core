# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.resource.view_types import ViewType
from peewee import CharField, ForeignKeyField

from ...core.model.db_field import JSONField
from ...experiment.experiment import Experiment
from ..resource_model import ResourceModel


class ViewHistoric(ModelWithUser):

    title = CharField()
    caption = CharField()
    view_type = EnumField(choices=ViewType)
    view_name = CharField()
    config_values = JSONField(null=False)
    transformers = JSONField(null=False)

    experiment: Experiment = ForeignKeyField(Experiment, null=True, index=True, on_delete='CASCADE')
    resource_model: ResourceModel = ForeignKeyField(ResourceModel, null=False, index=True, on_delete='CASCADE')

    _table_name = 'gws_view_historic'

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep, **kwargs)

        if self.experiment is not None:
            json_["experiment"] = {
                'id': self.experiment.id,
                'title': self.experiment.title
            }

        if self.resource_model is not None:
            json_["resource"] = {
                'id': self.resource_model.id,
                'name': self.resource_model.name
            }
        return json_
