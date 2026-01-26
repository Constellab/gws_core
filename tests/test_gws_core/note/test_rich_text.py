from gws_core import RichTextBlock, RichTextBlockTypeStandard
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataSpecial
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator
from gws_core.impl.rich_text.block.rich_text_block_figure import RichTextBlockFigure
from gws_core.impl.rich_text.block.rich_text_block_header import RichTextBlockHeaderLevel
from gws_core.impl.rich_text.block.rich_text_block_list import (
    RichTextBlockList,
    RichTextBlockListItem,
)
from gws_core.impl.rich_text.block.rich_text_block_paragraph import RichTextBlockParagraph
from gws_core.impl.rich_text.block.rich_text_block_view import RichTextBlockResourceView
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.test.base_test_case import BaseTestCase


@rich_text_block_decorator("Special")
class RichTextBlocSpecial(RichTextBlockDataSpecial):
    text: str

    def to_markdown(self) -> str:
        """Convert the iframe to markdown

        :return: the markdown representation of the iframe
        :rtype: str
        """
        return ""

    def to_html(self) -> str:
        return f"<p>Hello {self.text}</p>"


# test_rich_text
class TestRichText(BaseTestCase):
    def test_rich_text(self):
        rich_text: RichText = RichText()
        rich_text.add_header("Introduction", RichTextBlockHeaderLevel.HEADER_1)
        rich_text.add_figure(
            RichTextBlockFigure(
                filename="22ca8457-18b2-475f-aca6-19e7063d5e5e_1695039649929.png",
                width=1568,
                height=599,
                naturalWidth=1568,
                naturalHeight=599,
                title="",
                caption="",
            )
        )
        rich_text.add_paragraph(
            'Place for <te-variable-inline data-jsondata=\'{"name": "test2", "description": "", "type": "string", "value": null}\'></te-variable-inline> variable'
        )
        rich_text.add_paragraph(
            'Place for <te-variable-inline data-jsondata=\'{"name": "test3", "description": "", "type": "string", "value": null}\'></te-variable-inline> variable'
        )
        rich_text.add_paragraph(
            '<te-variable-inline data-jsondata=\'{"name": "figure_1", "description": "", "type": "string", "value": null}\'> figure_1</te-variable-inline>'
        )
        rich_text.add_paragraph(
            'Variable : <te-variable-inline data-jsondata=\'{"name": "figure_2", "description": "", "type": "string", "value": null}\'> figure_2</te-variable-inline> super'
        )
        rich_text.add_paragraph("End")

        self.assertFalse(rich_text.is_empty())

        figures = rich_text.get_figures_data()
        self.assertEqual(len(figures), 1)
        self.assertEqual(
            figures[0].filename, "22ca8457-18b2-475f-aca6-19e7063d5e5e_1695039649929.png"
        )

        resource_views = rich_text.get_resource_views_data()
        self.assertEqual(len(resource_views), 0)

        associated_resources = rich_text.get_associated_resources()
        self.assertEqual(len(associated_resources), 0)

        rich_text.set_parameter("test2", "test2_value")
        self.assertEqual(
            rich_text.to_dto().blocks[2].data["text"],
            'Place for <te-variable-inline data-jsondata=\'{"name": "test2", "description": "", "value": "test2_value", "type": "string"}\'></te-variable-inline> variable',
        )

        rich_text.set_parameter("test3", "test_3_value", replace_block=True)
        self.assertEqual(
            rich_text.to_dto().blocks[3].data["text"], "Place for test_3_value variable"
        )

        # test views
        view = RichTextBlockResourceView(
            id="1",
            resource_id="1",
            scenario_id="1",
            view_method_name="test_view",
            view_config={},
            title="title",
            caption="caption",
            view_config_id="1",
        )

        # add the resource view in the rich text at a specific variable
        block_count = len(rich_text.to_dto().blocks)
        rich_text.add_resource_view(view, "figure_1")
        # no block should be added
        self.assertEqual(len(rich_text.to_dto().blocks), block_count)
        self.assertTrue(
            rich_text.to_dto().blocks[4].is_type(RichTextBlockTypeStandard.RESOURCE_VIEW)
        )

        # add the resource view in the rich text at a specific variable
        # this should split the block in 3 blocks
        rich_text.add_resource_view(view, "figure_2")
        self.assertEqual(rich_text.to_dto().blocks[5].data["text"], "Variable : ")
        self.assertTrue(
            rich_text.to_dto().blocks[6].is_type(RichTextBlockTypeStandard.RESOURCE_VIEW)
        )
        self.assertEqual(rich_text.to_dto().blocks[7].data["text"], " super")
        self.assertEqual(rich_text.to_dto().blocks[8].data["text"], "End")

        # test replace block
        rich_text.replace_block_at_index(
            0, RichTextBlock.from_data(RichTextBlockParagraph(text="NewContent"))
        )

        # test replace views block with variables
        rich_text.replace_resource_views_with_parameters()
        # TODO check to improve
        self.assertTrue(rich_text.to_dto().blocks[4].is_type(RichTextBlockTypeStandard.PARAGRAPH))

    def test_is_empty(self):
        rich_text = RichText()
        self.assertTrue(rich_text.is_empty())

        rich_text.add_paragraph("")
        self.assertTrue(rich_text.is_empty())
        rich_text.add_paragraph("test")
        self.assertFalse(rich_text.is_empty())

    # def test_text_transcription(self):
    #     """Test the text transcription to rich text (with commands)
    #     """
    #     transcription_text = "Bonjour je m'appelle Jean. Enchanté de vous rencontrer. Titre présentation. Sous-titre détails de la commande. Liste banane, pomme, sous-élément pépin, peau, fin sous-élément poire fin liste. Nous allons faire la recette."

    #     result = RichTextTranscriptionService.transcribe_text_to_rich_text(transcription_text)

    #     expected_blocks = [
    #         {"id": "1", "type": "paragraph", "data": {"text": "Bonjour je m\'appelle Jean. Enchanté de vous rencontrer."}},
    #         {"id": "2", "type": "header", "data": {"text": "Présentation", "level": 2}},
    #         {"id": "3", "type": "header", "data": {"text": "Détails de la commande", "level": 3}},
    #         {"id": "4", "type": "list", "data": {
    #             "items": [
    #                 {"content": "banane", "items": []},
    #                 {"content": "pomme", "items": [
    #                     {"content": "pépin", "items": []},
    #                     {"content": "peau", "items": []}
    #                 ]},
    #                 {"content": "poire", "items": []}
    #             ],
    #             "style": "unordered"}
    #          },
    #         {"id": "5", "type": "paragraph", "data": {"text": "Nous allons faire la recette."}}]

    #     self.assert_json(result.to_dto_json_dict().get('blocks'), expected_blocks, ['id'])

    def test_to_markdown(self):
        """Test the conversion to markdown"""
        rich_text = RichText()
        rich_text.add_paragraph(
            'test <b>bold</b> <i>italic</i> <u>underline</u> <strike>strikethrough</strike> <a href="https://www.google.com">link</a>'
        )
        rich_text.add_header("header", RichTextBlockHeaderLevel.HEADER_1)

        list_block = RichTextBlockList(
            style="unordered",
            items=[
                RichTextBlockListItem(
                    content="item 1",
                    items=[
                        RichTextBlockListItem(content="sub item 1", items=[]),
                        RichTextBlockListItem(content="sub item 2", items=[]),
                    ],
                )
            ],
        )
        rich_text.add_list(list_block)

        result = rich_text.to_markdown()

        expected_result = """test **bold** *italic* __underline__ ~~strikethrough~~ [link](https://www.google.com)

## header

- item 1
  - sub item 1
  - sub item 2
"""
        self.assertEqual(result, expected_result)

    def test_diff_no_changes(self):
        """Test diff between two identical rich texts returns no changes."""
        rt1 = RichText()
        rt1.add_paragraph("Hello")
        rt1.add_header("Title", RichTextBlockHeaderLevel.HEADER_1)

        # Build a second rich text with the same block ids and content
        rt2 = RichText.from_json(rt1.to_dto_json_dict())

        diff = rt1.diff(rt2)
        self.assertFalse(diff.has_changes())
        self.assertEqual(len(diff.added), 0)
        self.assertEqual(len(diff.deleted), 0)
        self.assertEqual(len(diff.modified), 0)

    def test_diff_added_blocks(self):
        """Test diff detects blocks that were added."""
        rt1 = RichText()
        rt1.add_paragraph("Hello")

        rt2 = RichText()
        # Copy existing block
        old_block = rt1.get_blocks()[0]
        rt2.append_block(RichTextBlock(id=old_block.id, type=old_block.type, data=old_block.data))
        # Add a new block
        new_block = rt2.add_paragraph("New paragraph")

        diff = rt1.diff(rt2)
        self.assertTrue(diff.has_changes())
        self.assertEqual(len(diff.added), 1)
        self.assertEqual(len(diff.deleted), 0)
        self.assertEqual(len(diff.modified), 0)
        self.assertEqual(diff.added[0].block.id, new_block.id)
        self.assertEqual(diff.added[0].index, 1)

    def test_diff_deleted_blocks(self):
        """Test diff detects blocks that were deleted."""
        rt1 = RichText()
        block_a = rt1.add_paragraph("Keep me")
        block_b = rt1.add_paragraph("Delete me")

        rt2 = RichText()
        rt2.append_block(RichTextBlock(id=block_a.id, type=block_a.type, data=block_a.data))

        diff = rt1.diff(rt2)
        self.assertTrue(diff.has_changes())
        self.assertEqual(len(diff.added), 0)
        self.assertEqual(len(diff.deleted), 1)
        self.assertEqual(len(diff.modified), 0)
        self.assertEqual(diff.deleted[0].block.id, block_b.id)
        self.assertEqual(diff.deleted[0].index, 1)

    def test_diff_modified_blocks(self):
        """Test diff detects blocks whose data changed but type stayed the same."""
        rt1 = RichText()
        block_a = rt1.add_paragraph("Original text")

        rt2 = RichText()
        rt2.append_block(
            RichTextBlock(
                id=block_a.id,
                type=block_a.type,
                data={"text": "Modified text"},
            )
        )

        diff = rt1.diff(rt2)
        self.assertTrue(diff.has_changes())
        self.assertEqual(len(diff.added), 0)
        self.assertEqual(len(diff.deleted), 0)
        self.assertEqual(len(diff.modified), 1)
        self.assertEqual(diff.modified[0].block_id, block_a.id)
        self.assertEqual(diff.modified[0].old_block.data["text"], "Original text")
        self.assertEqual(diff.modified[0].new_block.data["text"], "Modified text")
        self.assertEqual(diff.modified[0].old_index, 0)
        self.assertEqual(diff.modified[0].new_index, 0)

    def test_diff_type_change_treated_as_delete_plus_add(self):
        """Test that a block with the same id but different type is treated as deleted + added."""
        rt1 = RichText()
        block_a = rt1.add_paragraph("Some text")

        # Create a header block reusing the same id
        rt2 = RichText()
        rt2.append_block(
            RichTextBlock(
                id=block_a.id,
                type="header",
                data={"text": "Some text", "level": 2},
            )
        )

        diff = rt1.diff(rt2)
        self.assertTrue(diff.has_changes())
        self.assertEqual(len(diff.modified), 0)
        self.assertEqual(len(diff.deleted), 1)
        self.assertEqual(len(diff.added), 1)
        self.assertEqual(diff.deleted[0].block.id, block_a.id)
        self.assertEqual(diff.deleted[0].block.type, "paragraph")
        self.assertEqual(diff.added[0].block.id, block_a.id)
        self.assertEqual(diff.added[0].block.type, "header")

    def test_diff_mixed_changes(self):
        """Test diff with a combination of added, deleted, and modified blocks."""
        rt1 = RichText()
        block_a = rt1.add_paragraph("Unchanged")
        block_b = rt1.add_paragraph("Will be modified")
        block_c = rt1.add_paragraph("Will be deleted")

        rt2 = RichText()
        # block_a unchanged
        rt2.append_block(RichTextBlock(id=block_a.id, type=block_a.type, data=block_a.data))
        # block_b modified
        rt2.append_block(
            RichTextBlock(
                id=block_b.id,
                type=block_b.type,
                data={"text": "Has been modified"},
            )
        )
        # block_c not present → deleted
        # new block added
        new_block = rt2.add_paragraph("Brand new")

        diff = rt1.diff(rt2)
        self.assertTrue(diff.has_changes())
        self.assertEqual(len(diff.deleted), 1)
        self.assertEqual(len(diff.added), 1)
        self.assertEqual(len(diff.modified), 1)

        self.assertEqual(diff.deleted[0].block.id, block_c.id)
        self.assertEqual(diff.added[0].block.id, new_block.id)
        self.assertEqual(diff.modified[0].block_id, block_b.id)

    def test_diff_both_empty(self):
        """Test diff between two empty rich texts."""
        rt1 = RichText()
        rt2 = RichText()

        diff = rt1.diff(rt2)
        self.assertFalse(diff.has_changes())

    def test_diff_old_empty(self):
        """Test diff when old is empty and new has blocks."""
        rt1 = RichText()
        rt2 = RichText()
        new_block = rt2.add_paragraph("New")

        diff = rt1.diff(rt2)
        self.assertTrue(diff.has_changes())
        self.assertEqual(len(diff.added), 1)
        self.assertEqual(len(diff.deleted), 0)
        self.assertEqual(diff.added[0].block.id, new_block.id)

    def test_diff_new_empty(self):
        """Test diff when new is empty and old has blocks."""
        rt1 = RichText()
        block = rt1.add_paragraph("Old")
        rt2 = RichText()

        diff = rt1.diff(rt2)
        self.assertTrue(diff.has_changes())
        self.assertEqual(len(diff.deleted), 1)
        self.assertEqual(len(diff.added), 0)
        self.assertEqual(diff.deleted[0].block.id, block.id)

    def test_convert_special_blocks(self):
        """Test that special blocks are converted to HTML blocks when calling to_dto"""
        rich_text = RichText()

        # Add a special block (RichTextBlocSpecial extends RichTextBlockDataSpecial)
        special_block = RichTextBlock.from_data(RichTextBlocSpecial(text="World"))
        rich_text.append_block(special_block)

        # Convert to JSON and reload
        json_dict = rich_text.to_dto_json_dict()
        reloaded_rich_text = RichText.from_json(json_dict)

        # Without convert_special_blocks, the block type should remain "Special"
        dto_without_conversion = reloaded_rich_text.to_dto(convert_special_blocks=False)
        self.assertEqual(
            dto_without_conversion.blocks[0].type, "RICH_TEXT_BLOCK.test_gws_core.Special"
        )

        # With convert_special_blocks, the block should be converted to HTML
        dto_with_conversion = reloaded_rich_text.to_dto(convert_special_blocks=True)
        self.assertEqual(dto_with_conversion.blocks[0].type, "html")
        self.assertEqual(dto_with_conversion.blocks[0].data["html"], "<p>Hello World</p>")
