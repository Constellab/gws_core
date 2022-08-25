
from typing import List

from gws_core import Experiment, Robot
from gws_core.config.config_types import ConfigParams
from gws_core.core.classes.rich_text_content import (RichTextI,
                                                     RichTextResourceView,
                                                     RichTextSpecialOps)
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.robot.robot_protocol import CreateSimpleRobot
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.project.project import Project
from gws_core.project.project_dto import ProjectDto
from gws_core.report.report import Report, ReportExperiment
from gws_core.report.report_dto import ReportDTO
from gws_core.report.report_resource import ReportResource
from gws_core.report.report_service import ReportService
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view_config.view_config_service import ViewConfigService
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

        content: RichTextI = {'ops': [{'insert': 'Hello'}]}
        report = ReportService.update_content(report.id, content)
        self.assert_json(report.content, content)

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

    def test_associated_resource(self):
        """ Test when we add a resource view, it created an associated resource for the report
        """
        # create report and resource
        report = ReportService.create(ReportDTO(title='Test report'))
        resource_model = ResourceModel.save_from_resource(Robot.empty(), ResourceOrigin.UPLOADED)

        # simulate the rich text with resource id
        rich_text_resource_view: RichTextResourceView = {
            "resource_id": resource_model.id,
        }
        operation = {"insert": {RichTextSpecialOps.RESOURCE_VIEW.value: rich_text_resource_view}}

        # update report content
        new_content = {"ops": [operation]}
        ReportService.update_content(report.id, new_content)

        # check that the associated resource is created
        report_resources = ReportResource.get_by_report(report.id)
        self.assertEqual(len(report_resources), 1)

        # test adding the same resource a second time it shouldn't create a new associated resource
        new_content = {"ops": [operation, operation]}
        ReportService.update_content(report.id, new_content)
        report_resources = ReportResource.get_by_report(report.id)
        self.assertEqual(len(report_resources), 1)

        # test removing the resource
        new_content = {"ops": []}
        ReportService.update_content(report.id, new_content)
        report_resources = ReportResource.get_by_report(report.id)
        self.assertEqual(len(report_resources), 0)

    # test to have a view config to a report
    async def test_add_view_config_to_report(self):
        # generate a resource from an experiment
        experiment = IExperiment()
        i_process = experiment.get_protocol().add_process(RobotCreate, 'create')
        await experiment.run()
        robot_model = i_process.get_output_resource_model('robot')

        # create a view config
        result = await ResourceService.call_view_on_resource_model(robot_model, "view_as_string", {}, [], True)

        report = ReportService.create(ReportDTO(title='Test report'))
        # add the view to the report
        ReportService.add_view_to_content(report.id, result["view_config"]["id"])

        # Retrieve the report rich text
        report_db = ReportService.get_by_id_and_check(report.id)
        rich_text = report_db.get_content_as_rich_text()

        # check that a resource view exist in the rich text
        resource_views: List[RichTextResourceView] = rich_text.get_resource_views()
        self.assertEqual(len(resource_views), 1)
        self.assertEqual(resource_views[0]['view_method_name'], "view_as_string")
        self.assertEqual(resource_views[0]['resource_id'], robot_model.id)

        # verify that the report was automatically associated with the experiment
        self.assertEqual(ReportExperiment.find_by_pk(experiment._experiment.id, report.id).count(), 1)
