# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.core.classes.rich_text_content import (RichText, RichTextI,
                                                     RichTextResourceViewData)
from gws_core.test.base_test_case_light import BaseTestCaseLight


# test_rich_text
class TestRichText(BaseTestCaseLight):

    def test_rich_text(self):

        rich_text_ops: RichTextI = RichText.create_rich_text_i([
            {
                "id": "0",
                "type": "header",
                "data": {
                        "text": "Introduction",
                        "level": 1
                }
            },
            {
                "id": "1",
                "type": "figure",
                "data": {
                        "filename": "22ca8457-18b2-475f-aca6-19e7063d5e5e_1695039649929.png",
                        "width": 1568,
                        "height": 599,
                        "naturalWidth": 1568,
                        "naturalHeight": 599,
                        "title": "",
                        "caption": ""
                }
            },
            {
                "id": "3",
                "type": "paragraph",
                "data": {
                        "text": "Place for $test2$ variable"
                }
            },
            {
                "id": "9",
                "type": "paragraph",
                "data": {
                        "text": "Variable : $figure_1$ super"
                }
            },
            {
                "id": "13",
                "type": "paragraph",
                "data": {
                        "text": "End"
                }
            }
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
        self.assertEqual(rich_text.get_content()['blocks'][2]['data']["text"],
                         'Place for test2_value variable')

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

        # add the resource in the rich text at a specific variable
        # this should split the block in 3 blocks
        rich_text.add_resource_views(view, 'figure_1')
        self.assertEqual(rich_text.get_content()['blocks'][3]['data']["text"], 'Variable : ')
        self.assertEqual(rich_text.get_content()['blocks'][4]['data']['id'], '1')
        self.assertEqual(rich_text.get_content()['blocks'][5]['data']["text"], ' super')
        self.assertEqual(rich_text.get_content()['blocks'][6]['data']["text"], 'End')
