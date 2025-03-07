

from gws_core import (RichTextBlock, RichTextBlockType, RichTextDTO,
                      RichTextParagraphData, RichTextResourceViewData)
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_transcription_service import \
    RichTextTranscriptionService
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
                id="2",
                type=RichTextBlockType.PARAGRAPH,
                data={
                    # Paragraph with a variable named test2
                    "text": 'Place for <te-variable-inline data-jsondata=\'{"name": "test2", "description": "", "type": "string", "value": null}\'></te-variable-inline> variable'
                }
            ),
            RichTextBlock(
                id="3",
                type=RichTextBlockType.PARAGRAPH,
                data={
                    # Paragraph with a variable named test2
                    "text": 'Place for <te-variable-inline data-jsondata=\'{"name": "test3", "description": "", "type": "string", "value": null}\'></te-variable-inline> variable'
                }
            ),
            # Variable for figure inline with text alone in a block
            RichTextBlock(
                id="4",
                type=RichTextBlockType.PARAGRAPH,
                data={
                    "text": '<te-variable-inline data-jsondata=\'{"name": "figure_1", "description": "", "type": "string", "value": null}\'> figure_1</te-variable-inline>'
                }
            ),
            #  Variable for figure inline with text
            RichTextBlock(
                id="5",
                type=RichTextBlockType.PARAGRAPH,
                data={
                    "text": 'Variable : <te-variable-inline data-jsondata=\'{"name": "figure_2", "description": "", "type": "string", "value": null}\'> figure_2</te-variable-inline> super'
                }
            ),
            RichTextBlock(
                id="6",
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

        rich_text.set_parameter('test2', 'test2_value')
        self.assertEqual(
            rich_text.to_dto().blocks[2].data["text"],
            'Place for <te-variable-inline data-jsondata=\'{"name": "test2", "description": "", "type": "string", "value": "test2_value"}\'></te-variable-inline> variable')

        rich_text.set_parameter('test3', 'test_3_value', replace_block=True)
        self.assertEqual(
            rich_text.to_dto().blocks[3].data["text"],
            'Place for test_3_value variable'
        )

        # test views
        view: RichTextResourceViewData = {
            "id": "1",
            "resource_id": "1",
            "scenario_id": "1",
            "view_method_name": "test_view",
            "view_config": {},
            "title": "title",
            "caption": "caption",
            "view_config_id": "1"
        }

        # add the resource view in the rich text at a specific variable
        block_count = len(rich_text.to_dto().blocks)
        rich_text.add_resource_view(view, 'figure_1')
        # no block should be added
        self.assertEqual(len(rich_text.to_dto().blocks), block_count)
        self.assertEqual(rich_text.to_dto().blocks[4].type, RichTextBlockType.RESOURCE_VIEW)

        # add the resource view in the rich text at a specific variable
        # this should split the block in 3 blocks
        rich_text.add_resource_view(view, 'figure_2')
        self.assertEqual(rich_text.to_dto().blocks[5].data["text"], 'Variable : ')
        self.assertEqual(rich_text.to_dto().blocks[6].type, RichTextBlockType.RESOURCE_VIEW)
        self.assertEqual(rich_text.to_dto().blocks[7].data["text"], ' super')
        self.assertEqual(rich_text.to_dto().blocks[8].data["text"], 'End')

        # test replace block
        rich_text.replace_block_at_index(0, RichTextBlock(
            id="0132",
            type=RichTextBlockType.PARAGRAPH,
            data={
                "text": "NewContent"
            }
        ))
        rich_text.to_dto().blocks[0].type = RichTextBlockType.PARAGRAPH

        # test replace views block with variables
        rich_text.replace_resource_views_with_parameters()
        # TODO check to improve
        self.assertEqual(rich_text.to_dto().blocks[4].type, RichTextBlockType.PARAGRAPH)

    def test_replace_data(self):

        rich_text: RichText = RichText()
        block = rich_text.add_paragraph("Introduction")

        new_data: RichTextParagraphData = {
            "text": "NewContent"
        }
        rich_text.replace_block_data_by_id(block.id, new_data)

        self.assertEqual(rich_text.to_dto().blocks[0].data["text"], "NewContent")
        self.assertEqual(len(rich_text.get_blocks()), 1)

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

    def test_text_transcription(self):
        """Test the text transcription to rich text (with commands)
        """
        transcription_text = "Bonjour je m'appelle Jean. Enchanté de vous rencontrer. Titre présentation. Sous-titre détails de la commande. Liste banane, pomme, sous-élément pépin, peau, fin sous-élément poire fin liste. Nous allons faire la recette."

        result = RichTextTranscriptionService.transcribe_text_to_rich_text(transcription_text)

        expected_blocks = [
            {"id": "1", "type": "paragraph", "data": {"text": "Bonjour je m\'appelle Jean. Enchanté de vous rencontrer."}},
            {"id": "2", "type": "header", "data": {"text": "Présentation", "level": 2}},
            {"id": "3", "type": "header", "data": {"text": "Détails de la commande", "level": 3}},
            {"id": "4", "type": "list", "data": {
                "items": [
                    {"content": "banane", "items": []},
                    {"content": "pomme", "items": [
                        {"content": "pépin", "items": []},
                        {"content": "peau", "items": []}
                    ]},
                    {"content": "poire", "items": []}
                ],
                "style": "unordered"}
             },
            {"id": "5", "type": "paragraph", "data": {"text": "Nous allons faire la recette."}}]

        self.assert_json(result.to_dto_json_dict().get('blocks'), expected_blocks, ['id'])
