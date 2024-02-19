# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import Robot
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import (RichTextBlockType,
                                                     RichTextDTO)
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.project.project import Project
from gws_core.project.project_dto import ProjectLevelStatus
from gws_core.report.report import Report, ReportExperiment
from gws_core.report.report_dto import ReportSaveDTO
from gws_core.report.report_service import ReportService
from gws_core.report.report_view_model import ReportViewModel
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.test.base_test_case import BaseTestCase


# test_report
class TestReport(BaseTestCase):

    def test_report(self):
        project = Project(title='Project', level_status=ProjectLevelStatus.LEAF).save()

        # test create an empty report
        report: Report = ReportService.create(ReportSaveDTO(title='Test report'))

        self.assertIsInstance(report, Report)
        self.assertEqual(report.title, 'Test report')

        report = ReportService.update(report.id, ReportSaveDTO(title='New title'))
        self.assertEqual(report.title, 'New title')

        content: RichTextDTO = RichText.create_rich_text_dto([RichText.create_paragraph('1', 'Hello world!')])
        ReportService.update_content(report.id, content)
        report = report.refresh()
        self.assertEqual(len(report.content.blocks), 1)

        experiment = ExperimentService.create_experiment()

        # Create a second experiment with a report
        experiment_2 = ExperimentService.create_experiment()
        report_2 = ReportService.create(ReportSaveDTO(title='Report 2'), [experiment_2.id])

        # Add exp 1 on report 1
        ReportService.add_experiment(report.id, experiment.id)
        reports = ReportService.get_by_experiment(experiment.id)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].id, report.id)

        # Check that report_2 ha an experiment
        reports = ReportService.get_by_experiment(experiment_2.id)
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0].id, report_2.id)

        # Check get experiment by report
        experiments = ReportService.get_experiments_by_report(report.id)
        self.assertEqual(len(experiments), 1)
        self.assertEqual(experiments[0].id, experiment.id)

        # Test remove experiment
        ReportService.remove_experiment(report.id, experiment.id)
        reports = ReportService.get_by_experiment(experiment.id)
        self.assertEqual(len(reports), 0)

        # Try to validate report_2, but there should be an error because the experiment is not validated
        self.assertRaises(Exception, ReportService._validate, report_2.id)
        experiment_2.is_validated = True
        experiment_2.project = project
        experiment_2.save()

        report_2 = ReportService._validate(report_2.id, project.id)
        self.assertTrue(report_2.is_validated)

        # Try to update report_2
        self.assertRaises(Exception, ReportService.update_content, report_2.id, {})

        # Add exp 1 on report 1 to delete it afterward
        ReportService.add_experiment(report.id, experiment.id)
        ReportService.delete(report.id)
        self.assertIsNone(Report.get_by_id(report.id))
        self.assertEqual(len(ReportService.get_experiments_by_report(report.id)), 0)

    def test_associated_views(self):
        """ Test when we add a resource view, it created an associated resource for the report
        """
        # create report and resource
        report = ReportService.create(ReportSaveDTO(title='Test report'))
        resource_model = ResourceModel.save_from_resource(Robot.empty(), ResourceOrigin.UPLOADED)

        view_result = ResourceService.call_view_on_resource_model(resource_model, "view_as_json", {}, True)

        # simulate the rich text with resource id
        rich_text_resource_view = view_result.view_config.to_rich_text_resource_view()
        block = RichText.create_block('1', RichTextBlockType.RESOURCE_VIEW, rich_text_resource_view)

        # update report content
        new_content = RichText.create_rich_text_dto([block])
        ReportService.update_content(report.id, new_content)

        # check that the associated ReportViewModel is created
        report_views = ReportViewModel.get_by_report(report.id)
        self.assertEqual(len(report_views), 1)

        # test get report by resource
        paginator = ReportService.get_by_resource(resource_model.id)
        # check result
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, report.id)

        # test adding the same resource a second time it shouldn't create a new associated view
        new_content = RichText.create_rich_text_dto([block, block])
        ReportService.update_content(report.id, new_content)
        report_views = ReportViewModel.get_by_report(report.id)
        self.assertEqual(len(report_views), 1)

        # test removing the resource
        new_content = RichText.create_rich_text_dto([])
        ReportService.update_content(report.id, new_content)
        report_views = ReportViewModel.get_by_report(report.id)
        self.assertEqual(len(report_views), 0)

    # test to have a view config to a report
    def test_add_view_config_to_report(self):
        # generate a resource from an experiment
        experiment = IExperiment()
        experiment.get_protocol().add_process(RobotCreate, 'create')
        experiment.run()

        i_process = experiment.get_protocol().get_process('create')
        robot_model = i_process.get_output_resource_model('robot')

        # create a view config
        result = ResourceService.call_view_on_resource_model(robot_model, "view_as_string", {}, True)

        report = ReportService.create(ReportSaveDTO(title='Test report'))
        # add the view to the report
        ReportService.add_view_to_content(report.id, result.view_config.id)

        # Retrieve the report rich text
        report_db = ReportService.get_by_id_and_check(report.id)
        rich_text = report_db.get_content_as_rich_text()

        # check that a view exist in the rich text
        resource_views = rich_text.get_resource_views_data()
        self.assertEqual(len(resource_views), 1)
        self.assertEqual(resource_views[0]['view_method_name'], "view_as_string")
        self.assertEqual(resource_views[0]['resource_id'], robot_model.id)

        # verify that the report was automatically associated with the experiment
        self.assertEqual(ReportExperiment.find_by_pk(experiment.get_experiment_model().id, report.id).count(), 1)

        with self.assertRaises(Exception):
            # Check that we cannot remove the experiment because of the view
            ReportService.remove_experiment(report.id, experiment.get_experiment_model().id)

        # remove the view from the report
        ReportService.update_content(report.id, RichText.create_rich_text_dto([]))

        # Check that we cannot remove the experiment because of the view
        ReportService.remove_experiment(report.id, experiment.get_experiment_model().id)
