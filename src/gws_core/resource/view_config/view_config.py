# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import List, Optional

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.core.utils.utils import Utils
from gws_core.resource.view_types import ViewType
from gws_core.tag.taggable_model import TaggableModel
from peewee import BooleanField, CharField, ForeignKeyField

from ...core.model.db_field import JSONField
from ...experiment.experiment import Experiment
from ..resource_model import ResourceModel


class ViewConfig(ModelWithUser, TaggableModel):

    title = CharField()
    view_type = EnumField(choices=ViewType)
    view_name = CharField()
    config_values = JSONField(null=False)
    transformers = JSONField(null=False)

    experiment: Experiment = ForeignKeyField(Experiment, null=True, index=True, on_delete='CASCADE')
    resource_model: ResourceModel = ForeignKeyField(ResourceModel, null=False, index=True, on_delete='CASCADE')

    flagged = BooleanField(default=False)

    _table_name = 'gws_view_config'

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep, **kwargs)

        json_["tags"] = self.get_tags_json()

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

    @classmethod
    def get_same_view_config(cls, view_config: 'ViewConfig') -> Optional['ViewConfig']:
        """return a view config that has same parameters

        :return: _description_
        :rtype: _type_
        """

        view_configs_db: List[ViewConfig] = list(ViewConfig.select().where(
            (ViewConfig.resource_model == view_config.resource_model) &
            (ViewConfig.view_name == view_config.view_name) &
            (ViewConfig.view_type == view_config.view_type)
        ))

        for view_config_db in view_configs_db:
            if Utils.json_equals(view_config_db.config_values, view_config.config_values) and \
                    Utils.json_equals(view_config_db.transformers, view_config.transformers):
                return view_config_db

        return None
