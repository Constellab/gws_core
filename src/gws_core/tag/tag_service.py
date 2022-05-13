
from typing import List, Type

from gws_core.core.exception.exceptions.not_found_exception import \
    NotFoundException
from gws_core.core.utils.utils import Utils

from ..core.classes.paginator import Paginator
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.model import Model
from ..model.typing_manager import TypingManager
from .tag import Tag, default_tags
from .tag_model import TagModel
from .taggable_model import TaggableModel


class TagService():

    @classmethod
    def init_default_tags(cls) -> None:
        """Create the default tags of the database if not prevent
        """
        if TagModel.select().count() > 0:
            return

        for key, value in default_tags.items():
            TagModel.create(key, value).save()

    @classmethod
    def register_tags(cls, tags: List[Tag]) -> List[TagModel]:
        tag_models: List[TagModel] = []
        for tag in tags:
            tag_models.append(cls.register_tag(tag.key, tag.value))
        return tag_models

    @classmethod
    def register_tag(cls, tag_key: str, tag_value: str) -> TagModel:
        tag: TagModel = TagModel.find_by_key(tag_key)

        if tag is None:
            tag = TagModel.create(tag_key)

        tag.add_value(tag_value)
        return tag.save()

    @classmethod
    def get_all_tags(cls,
                     page: int = 0,
                     number_of_items_per_page: int = 20) -> Paginator[TagModel]:
        query = TagModel.select().order_by(TagModel.key)
        return Paginator(query, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search_by_key(cls,
                      tag_key: str) -> List[TagModel]:
        return list(TagModel.select().where(TagModel.key.contains(tag_key)).order_by(TagModel.key))

    @classmethod
    def get_by_key(cls,
                   tag_key: str) -> TagModel:
        return TagModel.select().where(TagModel.key == tag_key).first()

    @classmethod
    @transaction()
    def add_tag_to_model(cls, model_type: Type[TaggableModel], id: str,
                         tag_key: str, tag_value: str) -> List[Tag]:

        if not Utils.issubclass(model_type, TaggableModel):
            raise BadRequestException("Can't add tags to this object type")

         # Add tag to resource model
        model: TaggableModel = model_type.get_by_id(id)

        if model is None:
            raise NotFoundException(f"Can't find model with id {id}")

        model.add_or_replace_tag(tag_key, tag_value)
        model.save()

        # add tag to the list of tags
        TagService.register_tag(tag_key, tag_value)

        return model.get_tags()

    @classmethod
    @transaction()
    def save_tags_to_model(cls, model_type: Type[TaggableModel], id: str,
                           tags: List[Tag]) -> List[Tag]:

        if not Utils.issubclass(model_type, TaggableModel):
            raise BadRequestException("Can't add tags to this object type")

        # Add tag to resource model
        model: TaggableModel = model_type.get_by_id(id)

        if model is None:
            raise NotFoundException(f"Can't find model with id {id}")

        for tag in tags:
            if model.has_tag(tag):
                continue

            # add tag to the list of tags
            TagService.register_tag(tag.key, tag.value)

        # set and save all tags
        model.set_tags(tags)
        model.save()

        return model.get_tags()
