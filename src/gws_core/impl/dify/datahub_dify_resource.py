

import json
from datetime import datetime
from typing import List, Optional, cast

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.settings import Settings
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_modification import RichTextAggregateDTO
from gws_core.impl.s3.s3_server_service import S3ServerService
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_search_builder import ResourceSearchBuilder
from gws_core.resource.resource_service import ResourceService
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag, TagOrigins
from gws_core.tag.tag_dto import TagOriginType
from gws_core.user.current_user_service import CurrentUserService


class DatahubDifyResource:
    """
    DatahubDifyResource is a class that wraps the resource object to manage
    the link between the datahub and the Dify app.
    """

    resource_model: ResourceModel

    _entity_tag_list: EntityTagList = None
    _tmp_dir: str = None

    # Tag key on resource to identify that it is sent to Dify
    # Value is the Dify document id
    DIFY_DOC_TAG_KEY = 'dify_document'
    # Tag key on resource to identify that it is sent to Dify
    # Value is the Dify knowledge base id
    DIFY_KB_TAG_KEY = 'dify_knowledge_base'
    # Tag key on resource to identify that it is sent to Dify
    # Value ISO date time of the last sync with Dify
    DIFY_SYNC_TAG_KEY = 'dify_sync'

    SUPPORTED_FILE_EXTENSIONS = ['txt', 'pdf', 'docx', 'doc',
                                 'md', 'msg', 'json']

    MAX_FILE_SIZE_MB = 15

    def __init__(self, resource_model: ResourceModel):
        self.resource_model = resource_model

    def is_compatible_with_dify(self) -> bool:
        """Check if the resource is compatible with Dify."""
        # Check if the resource is a file
        resource = self.resource_model.get_resource()
        if not isinstance(resource, File):
            return False

        if resource.extension not in self.SUPPORTED_FILE_EXTENSIONS:
            return False

        # If the file is a json, we only accept rich text json
        if resource.extension == 'json':
            try:
                dict_ = json.loads(resource.read())
                if not RichText.is_rich_text_json(dict_) and not RichTextAggregateDTO.json_is_rich_text_aggregate(dict_):
                    return False
            except json.JSONDecodeError as e:
                raise Exception(f"Error decoding JSON: {e}") from e

        # Check if the file size is less than 15 MB
        if resource.get_size() > self.MAX_FILE_SIZE_MB * 1024 * 1024:
            return False

        return True

    def get_dify_document_id(self) -> str | None:
        """Get the Dify document id from the resource tags."""
        resource_tags = self._get_tags()
        if not resource_tags.has_tag_key(self.DIFY_DOC_TAG_KEY):
            return None

        tags = resource_tags.get_tags_by_key(self.DIFY_DOC_TAG_KEY)
        return tags[0].tag_value

    def get_and_check_dify_document_id(self) -> str:
        """Get the Dify document id from the resource tags."""
        dify_document_id = self.get_dify_document_id()
        if dify_document_id is None:
            raise ValueError("The resource is not sent to Dify.")
        return dify_document_id

    def is_synced_with_dify(self) -> bool:
        """Check if the resource is synced with Dify."""
        resource_tags = self._get_tags()
        return resource_tags.has_tag_key(self.DIFY_DOC_TAG_KEY)

    def get_dify_sync_date(self) -> datetime | None:
        """Get the Dify sync date from the resource tags."""
        resource_tags = self._get_tags()
        if not resource_tags.has_tag_key(self.DIFY_SYNC_TAG_KEY):
            return None

        tags = resource_tags.get_tags_by_key(self.DIFY_SYNC_TAG_KEY)
        return DateHelper.from_utc_milliseconds(int(tags[0].tag_value))

    def get_and_check_dify_sync_date(self) -> datetime:
        """Get the Dify sync date from the resource tags and check if it is not None."""
        dify_sync_date = self.get_dify_sync_date()
        if dify_sync_date is None:
            raise ValueError("The resource is not sent to Dify.")
        return dify_sync_date

    def get_dify_knowledge_base_id(self) -> str:
        """Get the Dify knowledge base id from the resource tags."""
        resource_tags = self._get_tags()
        if not resource_tags.has_tag_key(self.DIFY_KB_TAG_KEY):
            raise ValueError("The resource was not sent to Dify.")

        tags = resource_tags.get_tags_by_key(self.DIFY_KB_TAG_KEY)
        return tags[0].tag_value

    def get_file_path(self) -> File:
        """Get the file path of the resource."""
        if not self.is_compatible_with_dify():
            raise ValueError("The resource is not compatible with Dify.")

        # For rech text, we convert it to a markdown file
        file = self._check_and_check_file()
        if file.extension == 'json':
            rich_text: RichText = None
            dict_ = json.loads(file.read())

            if RichText.is_rich_text_json(dict_):
                rich_text = RichText.from_json(dict_)
            elif RichTextAggregateDTO.json_is_rich_text_aggregate(dict_):
                aggregate_dto = RichTextAggregateDTO.from_json(dict_)
                rich_text = RichText(aggregate_dto.richText)
            else:
                raise ValueError("The json resource is not a rich text.")

            self._tmp_dir = Settings.make_temp_dir()
            file_path = f"{self._tmp_dir}/{file.name}.md"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(rich_text.to_markdown())

            return File(file_path)

        return cast(File, self.resource_model.get_resource())

    def get_chunk_separator(self, file_path: str) -> str:
        """Get the chunk separator for the resource."""
        extension = FileHelper.get_extension(file_path)
        # for markdown and json (because it is a rich text converted to md)
        if extension == 'md':
            return '## '

        return '\n\n'

    def mark_resource_as_sent_to_dify(self, dify_document_id: str, dify_knowledge_base_id: str) -> None:
        """Add tags to the resource."""
        resource_tags = self._get_tags()
        # Add the Dify document tag to the resource
        origins = TagOrigins(TagOriginType.USER, CurrentUserService.get_and_check_current_user().id)
        tags = [Tag(DatahubDifyResource.DIFY_DOC_TAG_KEY, dify_document_id, origins=origins),
                Tag(DatahubDifyResource.DIFY_KB_TAG_KEY, dify_knowledge_base_id, origins=origins),
                Tag(DatahubDifyResource.DIFY_SYNC_TAG_KEY, str(DateHelper.now_utc_as_milliseconds()), origins=origins)]
        resource_tags.replace_tags(tags)

    def unmark_resource_as_sent_to_dify(self) -> None:
        """Remove the Dify tags from the resource."""
        resource_tags = self._get_tags()
        entity_tags: List[EntityTag] = []
        entity_tags.extend(resource_tags.get_tags_by_key(self.DIFY_DOC_TAG_KEY))
        entity_tags.extend(resource_tags.get_tags_by_key(self.DIFY_KB_TAG_KEY))
        entity_tags.extend(resource_tags.get_tags_by_key(self.DIFY_SYNC_TAG_KEY))

        tags = [tag.to_simple_tag() for tag in entity_tags]

        resource_tags.delete_tags(tags)

    def is_up_to_date_in_dify(self) -> bool:
        """Check if the resource is up to date in Dify."""
        dify_sync_date = self.get_dify_sync_date()
        if dify_sync_date is None:
            return False
        return dify_sync_date >= self.resource_model.last_modified_at

    def _get_tags(self) -> EntityTagList:
        """Get the tags of the resource."""
        if self._entity_tag_list is None:
            self._entity_tag_list = EntityTagList.find_by_entity(EntityType.RESOURCE, self.resource_model.id)
        return self._entity_tag_list

    def _check_and_check_file(self) -> File:
        """Check if the resource is a file and return it."""
        resource = self.resource_model.get_resource()
        if not isinstance(resource, File):
            raise ValueError("The resource is not a file.")
        return resource

    def get_root_folder(self) -> SpaceFolder | None:
        """Get the root folder of the resource."""
        if not self.resource_model.folder:
            return None
        return self.resource_model.folder.get_root()

    def clear_tmp_dir(self) -> None:
        """Clear the tmp dir."""
        if self._tmp_dir is not None:
            FileHelper.delete_dir(self._tmp_dir)
            self._tmp_dir = None

    def get_datahub_key(self) -> str:
        """Get the datahub key of the resource."""
        tags = self._get_tags()
        if not tags.has_tag_key(S3ServerService.KEY_TAG_NAME):
            raise ValueError("Could not find the datahub key.")
        return tags.get_tags_by_key(S3ServerService.KEY_TAG_NAME)[0].tag_value

    @staticmethod
    def from_resource_model_id(resource_model_id: str) -> 'DatahubDifyResource':
        """Create a DatahubDifyResource from a resource model id."""
        resource_model = ResourceService.get_by_id_and_check(resource_model_id)
        return DatahubDifyResource(resource_model)

    @staticmethod
    def from_dify_document_id(dify_document_id: str) -> Optional['DatahubDifyResource']:
        """Create a DatahubDifyResource from a Dify document id."""
        # retrive all the files stored in the datahub
        research_search = ResourceSearchBuilder()
        research_search.add_tag_filter(Tag(DatahubDifyResource.DIFY_DOC_TAG_KEY, dify_document_id))
        resource_model = research_search.search_first()

        if not resource_model:
            return None

        return DatahubDifyResource(resource_model)
