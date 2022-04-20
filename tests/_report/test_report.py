
from typing import List

from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.project.project import Project
from gws_core.project.project_dto import ProjectDto
from gws_core.report.report import Report
from gws_core.report.report_dto import ReportDTO
from gws_core.report.report_service import ReportService
from gws_core.test.base_test_case import BaseTestCase


class TestReport(BaseTestCase):

    def test_report(self):
        project = Project()
        project.title = 'Project'
        project = project.save()
        # test create an empty report

        report = ReportService.create(ReportDTO(title='Test report'))

        self.assertIsInstance(report, Report)
        self.assertEqual(report.title, 'Test report')

        report = ReportService.update(report.id, ReportDTO(title='New title'))
        self.assertEqual(report.title, 'New title')

        report = ReportService.update_content(report.id, {'hello': 'nice'})
        self.assert_json(report.content, {'hello': 'nice'})

        experiment: Experiment = ExperimentService.create_empty_experiment()

        # Create a second experiment with a report
        experiment_2: Experiment = ExperimentService.create_empty_experiment()
        report_2 = ReportService.create(ReportDTO(title='Report 2'), [experiment_2.id])

        # Add exp 1 on report 1
        ReportService.add_experiment(report.id, experiment.id)
        reports: List[Report] = ReportService.get_by_experiment(experiment.id)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].id, report.id)

        # Check that report_2 ha an experiment
        reports: List[Report] = ReportService.get_by_experiment(experiment_2.id)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].id, report_2.id)

        # Check get experiment by report
        experiments: List[Experiment] = ReportService.get_experiments_by_report(report.id)
        self.assertEqual(len(experiments), 1)
        self.assertEqual(experiments[0].id, experiment.id)

        # Test remove experiment
        ReportService.remove_experiment(report.id, experiment.id)
        reports: List[Report] = ReportService.get_by_experiment(experiment.id)
        self.assertEqual(len(reports), 0)

        # Try to validate report_2, but there should be an error because the experiment is not validated
        self.assertRaises(Exception, ReportService.validate, report_2.id)
        experiment_2.is_validated = True
        experiment_2.project = project
        experiment_2.save()

        project_dto = ProjectDto(id=project.id, title=project.title)
        report_2 = ReportService.validate(report_2.id, project_dto=project_dto)
        self.assertTrue(report_2.is_validated)

        # Try to update report_2
        self.assertRaises(Exception, ReportService.update_content, report_2.id, {})

        # Add exp 1 on report 1 to delete it afterward
        ReportService.add_experiment(report.id, experiment.id)
        ReportService.delete(report.id)
        self.assertIsNone(Report.get_by_id(report.id))
        self.assertEqual(len(ReportService.get_experiments_by_report(report.id)), 0)
