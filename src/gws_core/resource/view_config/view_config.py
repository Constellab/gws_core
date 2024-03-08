# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import Any, List, Optional

from peewee import BooleanField, CharField, ForeignKeyField, ModelSelect

from gws_core.config.config import Config
from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.classes.enum_field import EnumField
from gws_core.core.decorator.transaction import transaction
from gws_core.core.model.db_field import BaseDTOField
from gws_core.core.model.model import Model
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.utils import Utils
from gws_core.entity_navigator.entity_navigator_type import (EntityType,
                                                             NavigableEntity)
from gws_core.impl.rich_text.rich_text_types import RichTextResourceViewData
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.view.view_types import ViewType
from gws_core.resource.view_config.view_config_dto import ViewConfigDTO
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.taggable_model import TaggableModel

from ...experiment.experiment import Experiment
from ..resource_model import ResourceModel


class ViewConfig(ModelWithUser, TaggableModel, NavigableEntity):

    title = CharField()
    view_type: ViewType = EnumField(choices=ViewType)
    view_name = CharField()
    config: Config = ForeignKeyField(Config, null=True, backref='+')

    experiment: Experiment = ForeignKeyField(Experiment, null=True, index=True, on_delete='CASCADE')
    resource_model: ResourceModel = ForeignKeyField(ResourceModel, null=False, index=True, on_delete='CASCADE')

    is_favorite = BooleanField(default=False)

    style: TypingStyle = BaseDTOField(TypingStyle, null=True)

    _table_name = 'gws_view_config'

    def to_dto(self) -> ViewConfigDTO:
        return ViewConfigDTO(
            id=self.id,
            created_at=self.created_at,
            created_by=self.created_by.to_dto(),
            last_modified_at=self.last_modified_at,
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
            view_type=self.view_type,
            view_name=self.view_name,
            is_favorite=self.is_favorite,
            config_values=self.get_config_values(),
            experiment=self.experiment.to_simple_dto() if self.experiment else None,
            resource=self.resource_model.to_simple_dto() if self.resource_model else None,
            style=self.style if self.style else self.view_type.get_typing_style()
        )

    def get_config_values(self) -> ConfigParamsDict:
        return self.config.get_values()

    def get_entity_name(self) -> str:
        return self.title

    def get_entity_type(self) -> EntityType:
        return EntityType.VIEW

    @transaction()
    def save(self, *args, **kwargs) -> Model:
        self.config.save()
        return super().save(*args, **kwargs)

    def delete_instance(self, *args, **kwargs) -> Any:
        if self.config is not None:
            self.config.delete_instance()
        result = super().delete_instance(*args, **kwargs)
        EntityTagList.delete_by_entity(EntityType.VIEW, self.id)
        return result

    def to_rich_text_resource_view(self, title: str = None, caption: str = None) -> RichTextResourceViewData:
        return {
            "id": self.id + "_" + str(DateHelper.now_utc_as_milliseconds()),  # generate a unique id
            "view_config_id": self.id,
            "resource_id": self.resource_model.id,
            "experiment_id": self.experiment.id if self.experiment else None,
            "view_method_name": self.view_name,
            "view_config": self.get_config_values(),
            "title": title or self.title,
            "caption": caption or "",
        }

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
    def get_by_resources(cls, resource_model_ids: List[str]) -> ModelSelect:
        return ViewConfig.select().where(ViewConfig.resource_model.in_(resource_model_ids))

    @classmethod
    def get_by_resource_and_favorite(cls, resource_model_id: str) -> ModelSelect:
        return ViewConfig.select().where((ViewConfig.resource_model == resource_model_id) & (ViewConfig.is_favorite == True))

    @classmethod
    def delete_by_resource(cls, resource_model_id: str) -> None:
        view_configs: List[ViewConfig] = list(ViewConfig.get_by_resource(resource_model_id))
        for view_config in view_configs:
            view_config.delete_instance()

    class Meta:
        table_name = 'gws_view_config'
