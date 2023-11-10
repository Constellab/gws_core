# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import List, Optional

from peewee import BooleanField, CharField, ForeignKeyField, ModelSelect

from gws_core.config.config import Config
from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.classes.enum_field import EnumField
from gws_core.core.classes.rich_text_content import RichTextResourceView
from gws_core.core.decorator.transaction import transaction
from gws_core.core.model.model import Model
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.utils import Utils
from gws_core.resource.view.view_types import ViewType
from gws_core.tag.taggable_model import TaggableModel

from ...core.model.db_field import JSONField
from ...experiment.experiment import Experiment
from ..resource_model import ResourceModel


class ViewConfig(ModelWithUser, TaggableModel):

    title = CharField()
    view_type = EnumField(choices=ViewType)
    view_name = CharField()
    config_values = JSONField(null=False)
    # TODO set null=False after update 0.5.8 and delete config_values
    config: Config = ForeignKeyField(Config, null=True, backref='+')

    experiment: Experiment = ForeignKeyField(Experiment, null=True, index=True, on_delete='CASCADE')
    resource_model: ResourceModel = ForeignKeyField(ResourceModel, null=False, index=True, on_delete='CASCADE')

    flagged = BooleanField(default=False)

    _table_name = 'gws_view_config'

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep, **kwargs)

        json_['config_values'] = self.get_config_values()

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

    def get_config_values(self) -> ConfigParamsDict:
        return self.config.get_values()

    @transaction()
    def save(self, *args, **kwargs) -> Model:
        self.config.save()
        return super().save(*args, **kwargs)

    def delete_instance(self, *args, **kwargs) -> int:
        if self.config is not None:
            self.config.delete_instance()
        return super().delete_instance(*args, **kwargs)

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
            if Utils.json_equals(view_config_db.config.get_values(), view_config.config.get_values()):
                return view_config_db

        return None

    @classmethod
    def get_by_resource(cls, resource_model_id: str) -> ModelSelect:
        return ViewConfig.select().where(ViewConfig.resource_model == resource_model_id)

    @classmethod
    def get_by_resource_and_flagged(cls, resource_model_id: str) -> ModelSelect:
        return ViewConfig.select().where((ViewConfig.resource_model == resource_model_id) & (ViewConfig.flagged == True))

    @classmethod
    def delete_by_resource(cls, resource_model_id: str) -> None:
        view_configs: List[ViewConfig] = list(ViewConfig.get_by_resource(resource_model_id))
        for view_config in view_configs:
            view_config.delete_instance()

    def to_rich_text_resource_view(self, title: str = None, caption: str = None) -> RichTextResourceView:
        return {
            "id": self.id + "_" + str(DateHelper.now_utc_as_milliseconds()),  # generate a unique id
            "resource_id": self.resource_model.id,
            "experiment_id": self.experiment.id if self.experiment else None,
            "view_method_name": self.view_name,
            "view_config": self.get_config_values(),
            "title": title or self.title,
            "caption": caption or "",
        }
