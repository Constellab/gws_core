

from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import (RichTextBlock,
                                                     RichTextBlockType,
                                                     RichTextDTO,
                                                     RichTextResourceViewData)
from gws_core.test.base_test_case_light import BaseTestCaseLight


# test_rich_text
class TestRichText(BaseTestCaseLight):

    def test_rich_text(self):

        rich_text_ops: RichTextDTO = RichText.create_rich_text_dto([
            RichTextBlock(
                id="0",
                type=RichTextBlockType.HEADER,
                data={
                    "text": "Introduction",
                    "level": 1
                }
            ),
            RichTextBlock(
                id="1",
                type=RichTextBlockType.FIGURE,
                data={
                    "filename": "22ca8457-18b2-475f-aca6-19e7063d5e5e_1695039649929.png",
                    "width": 1568,
                    "height": 599,
                    "naturalWidth": 1568,
                    "naturalHeight": 599,
                    "title": "",
                    "caption": ""
                }
            ),
            RichTextBlock(
                id="3",
                type=RichTextBlockType.PARAGRAPH,
                data={
                    # Paragraph with a variable named test2
                    "text": 'Place for <te-variable-inline data-jsondata=\'{"name": "test2", "description": "", "type": "string", "value": null}\'></te-variable-inline> variable'
                }
            ),
            RichTextBlock(
                id="9",
                type=RichTextBlockType.PARAGRAPH,
                data={
                    "text": 'Variable : <te-variable-inline data-jsondata=\'{"name": "figure_1", "description": "", "type": "string", "value": null}\'></te-variable-inline> super'
                }
            ),
            RichTextBlock(
                id="13",
                type=RichTextBlockType.PARAGRAPH,
                data={
                    "text": "End"
                }
            )
        ])

        rich_text: RichText = RichText(rich_text_ops)

        self.assertFalse(rich_text.is_empty())

        figures = rich_text.get_figures_data()
        self.assertEqual(len(figures), 1)
        self.assertEqual(figures[0]['filename'], '22ca8457-18b2-475f-aca6-19e7063d5e5e_1695039649929.png')

        resource_views = rich_text.get_resource_views_data()
        self.assertEqual(len(resource_views), 0)

        associated_resources = rich_text.get_associated_resources()
        self.assertEqual(len(associated_resources), 0)

        rich_text.replace_variable('test2', 'test2_value')
        self.assertEqual(
            rich_text.get_content().blocks[2].data["text"],
            'Place for <te-variable-inline data-jsondata=\'{"name": "test2", "description": "", "type": "string", "value": "test2_value"}\'></te-variable-inline> variable')

        # test views
        view: RichTextResourceViewData = {
            "id": "1",
            "resource_id": "1",
            "experiment_id": "1",
            "view_method_name": "test_view",
            "view_config": {},
            "title": "title",
            "caption": "caption",
            "view_config_id": "1"
        }

        # add the resource view in the rich text at a specific variable
        # this should split the block in 3 blocks
        rich_text.add_resource_views(view, 'figure_1')
        self.assertEqual(rich_text.get_content().blocks[3].data["text"], 'Variable : ')
        self.assertEqual(rich_text.get_content().blocks[4].type, RichTextBlockType.RESOURCE_VIEW)
        self.assertEqual(rich_text.get_content().blocks[5].data["text"], ' super')
        self.assertEqual(rich_text.get_content().blocks[6].data["text"], 'End')

        # test replace block
        rich_text.replace_block_at_index(0, RichTextBlock(
            id="0132",
            type=RichTextBlockType.PARAGRAPH,
            data={
                "text": "NewContent"
            }
        ))
        rich_text.get_content().blocks[0].type = RichTextBlockType.PARAGRAPH

        # test replace views block with variables
        rich_text.replace_resource_views_with_variables()
        # TODO check to improve
        self.assertEqual(rich_text.get_content().blocks[4].type, RichTextBlockType.PARAGRAPH)

    def test_is_empty(self):
        rich_text = RichText()
        self.assertTrue(rich_text.is_empty())

        rich_text = RichText(RichText.create_rich_text_dto([
            RichTextBlock(
                id="0",
                type=RichTextBlockType.PARAGRAPH,
                data={
                    "text": "Introduction"
                }
            )
        ]))
        self.assertFalse(rich_text.is_empty())

        rich_text = RichText(RichText.create_rich_text_dto([
            RichTextBlock(
                id="0",
                type=RichTextBlockType.PARAGRAPH,
                data={
                    "text": ""
                }
            )
        ]))
        self.assertTrue(rich_text.is_empty())
