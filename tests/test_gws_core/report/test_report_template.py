# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.report.template.report_template_service import \
    ReportTemplateService
from gws_core.test.base_test_case import BaseTestCase


# test_report_template
class TestReportTemplate(BaseTestCase):

    def test_create_empty(self):
        report_template = ReportTemplateService.create_empty('title')
        self.assertEqual(report_template.title, 'title')
        self.assertIsInstance(report_template.content, dict)
        self.assertEqual(report_template.content['blocks'], [])

    # def test_create_from_report(self):
    #     report = self.create_report()
    #     report_template = self.create_report_template_from_report(report.id)
    #     self.assertEqual(report_template.title, report.title)
    #     self.assertEqual(report_template.content, report.content)
