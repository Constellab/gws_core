# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.core.classes.rich_text_content import (RichText,
                                                     RichTextResourceView)
from gws_core.test.base_test_case_light import BaseTestCaseLight


# test_rich_text
class TestRichText(BaseTestCaseLight):

    def test_rich_text(self):

        rich_text_ops = {
            "ops": [
                {
                    "insert": "Introduction"
                },
                {
                    "attributes": {
                        "header": {
                            "level": 1,
                            "id": "introduction"
                        }
                    },
                    "insert": "\n"
                },
                {
                    "insert": {
                        "figure": {
                            "filename": "22ca8457-18b2-475f-aca6-19e7063d5e5e_1695039649929.png",
                            "width": 1568,
                            "height": 599,
                            "naturalWidth": 1568,
                            "naturalHeight": 599,
                            "title": "",
                            "caption": ""
                        }
                    }
                },
                {
                    "insert": "\nPlace for $test2$ variable\n\nConclusion"
                },
                {
                    "attributes": {
                        "header": {
                            "level": 1,
                            "id": "conclusion"
                        }
                    },
                    "insert": "\n"
                },
                {
                    "insert": "\n\nReferences"
                },
                {
                    "attributes": {
                        "header": {
                            "level": 1,
                            "id": "references"
                        }
                    },
                    "insert": "\n"
                },
                {
                    "insert": "Variable : $figure_1$ super\n\n\n"
                },
                {
                    "insert": "\nEnd"
                },
            ]
        }

        rich_text: RichText = RichText(rich_text_ops)

        self.assertFalse(rich_text.is_empty())

        figures = rich_text.get_figures()
        self.assertEqual(len(figures), 1)
        self.assertEqual(figures[0]['filename'], '22ca8457-18b2-475f-aca6-19e7063d5e5e_1695039649929.png')

        resource_views = rich_text.get_resource_views()
        self.assertEqual(len(resource_views), 0)

        associated_resources = rich_text.get_associated_resources()
        self.assertEqual(len(associated_resources), 0)

        rich_text.replace_variable('test2', 'test2_value')
        self.assertEqual(rich_text.get_content()['ops'][3]['insert'], '\nPlace for test2_value variable\n\nConclusion')

        # test views
        view: RichTextResourceView = {
            "id": "1",
            "resource_id": "1",
            "experiment_id": "1",
            "view_method_name": "test_view",
            "view_config": {},
            "title": "title",
            "caption": "caption"
        }

        # add the resource in the rich text at a specific variable
        # this should split the op in 3 ops
        rich_text.add_resource_views(view, 'figure_1')
        self.assertEqual(rich_text.get_content()['ops'][7]['insert'], 'Variable : \n')
        self.assertEqual(rich_text.get_content()['ops'][8]['insert']['resource_view']['id'], '1')
        self.assertEqual(rich_text.get_content()['ops'][9]['insert'], ' super\n\n\n')
        self.assertEqual(rich_text.get_content()['ops'][10]['insert'], '\nEnd')
