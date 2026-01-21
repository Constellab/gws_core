from abc import abstractmethod
from typing import Any, TypedDict

from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard

from .rich_text_types import RichTextDTO


class RichTextListItem(TypedDict):
    """Object representing a list item in a rich text"""

    content: str
    items: list["RichTextListItem"]
    meta: dict


class TeRichTextMigrator:
    def migrate_rich_text(self, content: RichTextDTO) -> RichTextDTO:
        for block in content.blocks:
            block.data = self.migrate_block_data(block.type, block.data)
        content.version = self.get_target_version()
        return content

    @abstractmethod
    def migrate_block_data(self, block_type: str, block_data: Any) -> Any:
        pass

    @abstractmethod
    def get_target_version(self) -> int:
        pass

    @staticmethod
    def get_migrators(current_version: int, target_version: int) -> list["TeRichTextMigrator"]:
        if current_version > target_version:
            raise ValueError("Cannot migrate from newer version to older version")
        migrators: list[TeRichTextMigrator] = []
        all_migrators_sorted = [TeRichTextMigrator1To2()]

        for migrator in all_migrators_sorted:
            if current_version < migrator.get_target_version() <= target_version:
                migrators.append(migrator)

        return migrators

    @staticmethod
    def migrate(rich_text: RichTextDTO, target_version: int) -> RichTextDTO:
        migrators = TeRichTextMigrator.get_migrators(rich_text.version, target_version)
        for migrator in migrators:
            rich_text = migrator.migrate_rich_text(rich_text)
        return rich_text


class TeRichTextMigrator1To2(TeRichTextMigrator):
    def migrate_block_data(self, block_type: RichTextBlockTypeStandard, block_data: Any) -> Any:
        if block_type == RichTextBlockTypeStandard.LIST:
            return self.migrate_list_item(block_data)
        return block_data

    def migrate_list_item(self, list_item: RichTextListItem) -> RichTextListItem:
        if list_item is None:
            return None
        if "meta" not in list_item:
            list_item["meta"] = {}

        if "items" not in list_item:
            list_item["items"] = []

        for child in list_item["items"]:
            self.migrate_list_item(child)
        return list_item

    def get_target_version(self) -> int:
        return 2
