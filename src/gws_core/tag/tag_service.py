
from typing import List

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

        # tt = list(TagModel.select().order_by(TagModel.key))
        # tt = list(TagModel.select(TagModel.key == tag_key).order_by(TagModel.key))
        return list(TagModel.select().where(TagModel.key.contains(tag_key)).order_by(TagModel.key))

    @classmethod
    @transaction()
    def add_tag_to_model(cls, model_typing_name: str, uri: str,
                         tag_key: str, tag_value: str) -> List[Tag]:

        # Add tag to resource model
        model: Model = TypingManager.get_object_with_typing_name_and_uri(model_typing_name, uri)

        if not isinstance(model, TaggableModel):
            raise BadRequestException("Can't add tags to this object type")

        model.add_or_replace_tag(tag_key, tag_value)
        model.save()

        # add tag to the list of tags
        TagService.register_tag(tag_key, tag_value)

        return model.get_tags()

    @classmethod
    @transaction()
    def save_tags_to_model(cls, model_typing_name: str, uri: str,
                           tags: List[Tag]) -> List[Tag]:

        # Add tag to resource model
        model: Model = TypingManager.get_object_with_typing_name_and_uri(model_typing_name, uri)

        if not isinstance(model, TaggableModel):
            raise BadRequestException("Can't add tags to this object type")

        for tag in tags:
            if model.has_tag(tag):
                continue

            # add tag to the list of tags
            TagService.register_tag(tag.key, tag.value)

        # set and save all tags
        model.set_tags(tags)
        model.save()

        return model.get_tags()
