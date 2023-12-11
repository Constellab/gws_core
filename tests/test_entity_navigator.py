# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.entity_navigator.entity_navigator import (
    EntityNavigatorExperiment, EntityNavigatorReport, EntityNavigatorResource,
    EntityNavigatorView)
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.protocol.protocol_interface import IProtocol
from gws_core.report.report import Report
from gws_core.report.report_dto import ReportSaveDTO
from gws_core.report.report_service import ReportService
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.test.base_test_case import BaseTestCase


# test_entity_navigator.py
class TestEntityNavigator(BaseTestCase):

    exp_1: Experiment
    exp_2: Experiment
    exp_3: Experiment

    exp_1_resource_1: ResourceModel
    exp_1_resource_2: ResourceModel
    exp_2_resource_1: ResourceModel
    exp_2_resource_2: ResourceModel
    exp_3_resource_1: ResourceModel

    exp_1_resource_1_view_1: ViewConfig

    # report associated to exp_1
    # report uses view exp_1_resource_1_view_1
    report_1: Report

    def test_entity_navigator(self):
        self._create_experiments()
        self._create_views()
        self._create_report()

        self._test_experiment_navigation()
        self._test_resource_navigation()
        self._test_view_navigation()
        self._test_report_navigation()
        self._test_recursive_navigation()

    def _create_experiments(self):
        # first experiment RobotCreate -> RobotMove
        experiment_1 = IExperiment()
        i_protocol_1: IProtocol = experiment_1.get_protocol()
        create_robot = i_protocol_1.add_task(RobotCreate, 'create_robot')
        move_robot_1 = i_protocol_1.add_task(RobotMove, 'move_robot')
        i_protocol_1.add_connector(create_robot >> 'robot', move_robot_1 << 'robot')
        experiment_1.run()

        create_robot.refresh()
        move_robot_1.refresh()

        robot_1 = create_robot.get_output_resource_model('robot')
        robot_2 = move_robot_1.get_output_resource_model('robot')

        # second experiment Input -> RobotMove
        experiment_2 = IExperiment()
        i_protocol_2: IProtocol = experiment_2.get_protocol()
        move_robot_2 = i_protocol_2.add_task(RobotMove, 'move_robot')
        move_robot_3 = i_protocol_2.add_task(RobotMove, 'move_robot_1')
        i_protocol_2.add_source('source_1', robot_1.id, move_robot_2 << 'robot')
        i_protocol_2.add_source('source_2', robot_2.id, move_robot_3 << 'robot')
        experiment_2.run()

        move_robot_2.refresh()
        move_robot_3.refresh()

        # Retrieve the models
        self.exp_1 = experiment_1.get_experiment_model()
        self.exp_2 = experiment_2.get_experiment_model()

        self.exp_1_resource_1 = create_robot.get_output_resource_model('robot')
        self.exp_1_resource_2 = move_robot_1.get_output_resource_model('robot')
        self.exp_2_resource_1 = move_robot_2.get_output_resource_model('robot')
        self.exp_2_resource_2 = move_robot_3.get_output_resource_model('robot')

        # third experiment exp_2_resource_2 -> RobotMove
        experiment_3 = IExperiment()
        i_protocol_3: IProtocol = experiment_3.get_protocol()
        move_robot_4 = i_protocol_3.add_task(RobotMove, 'move_robot')
        i_protocol_3.add_source('source_1', self.exp_2_resource_2.id, move_robot_4 << 'robot')
        experiment_3.run()

        move_robot_4.refresh()

        self.exp_3 = experiment_3.get_experiment_model()
        self.exp_3_resource_1 = move_robot_4.get_output_resource_model('robot')

    def _create_views(self):
        view_result = ResourceService.call_view_on_resource_model(self.exp_1_resource_1,
                                                                  'view_as_json', {}, True)
        self.exp_1_resource_1_view_1 = view_result.view_config

    def _create_report(self):
        report_1 = ReportService.create(ReportSaveDTO(title='test_report'))

        ReportService.add_experiment(report_1.id, self.exp_1.id)
        ReportService.add_view_to_content(report_1.id, self.exp_1_resource_1_view_1.id)

        self.report_1 = report_1.refresh()

    def _test_experiment_navigation(self):
        # Test get next experiment of experiment 1
        exp_nav = EntityNavigatorExperiment(self.exp_1)
        next_exps = exp_nav.get_next_experiments().get_entities_list()
        self.assertEqual(len(next_exps), 1)
        self.assertEqual(next_exps[0].id, self.exp_2.id)

        # Test get next resources of experiment 1
        next_resources = exp_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 2)
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_1_resource_1.id]))
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_1_resource_2.id]))

        # Test get next experiment of experiment 3
        exp_nav = EntityNavigatorExperiment(self.exp_3)
        next_exps = exp_nav.get_next_experiments().get_entities_list()
        self.assertEqual(len(next_exps), 0)

        # Test get next resources of experiment 2
        exp_nav = EntityNavigatorExperiment(self.exp_2)
        next_resources = exp_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 2)
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_2_resource_1.id]))
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_2_resource_2.id]))

        # Test get previous experiment of experiment 2
        exp_nav = EntityNavigatorExperiment(self.exp_2)
        prev_exps = exp_nav.get_previous_experiments().get_entities_list()
        self.assertEqual(len(prev_exps), 1)
        self.assertEqual(prev_exps[0].id, self.exp_1.id)

        # Test get previous resources of experiment 2
        exp_nav = EntityNavigatorExperiment(self.exp_2)
        prev_resources = exp_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 2)
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_1.id]))
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_2.id]))

        # Test get previous experiment of experiment 1
        exp_nav = EntityNavigatorExperiment(self.exp_1)
        prev_exps = exp_nav.get_previous_experiments().get_entities_list()
        self.assertEqual(len(prev_exps), 0)

        # Test get previous resources of experiment 1
        exp_nav = EntityNavigatorExperiment(self.exp_1)
        prev_resources = exp_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 0)

        # Test get next report of experiment 1
        exp_nav = EntityNavigatorExperiment(self.exp_1)
        next_reports = exp_nav.get_next_reports().get_entities_list()
        self.assertEqual(len(next_reports), 1)
        self.assertEqual(next_reports[0].id, self.report_1.id)

        # Test get next report of experiment 2
        exp_nav = EntityNavigatorExperiment(self.exp_2)
        next_reports = exp_nav.get_next_reports().get_entities_list()
        self.assertEqual(len(next_reports), 0)

        # Test get next view of experiment 1
        exp_nav = EntityNavigatorExperiment(self.exp_1)
        next_views = exp_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 1)
        self.assertEqual(next_views[0].id, self.exp_1_resource_1_view_1.id)

        # Test get next view of experiment 2
        exp_nav = EntityNavigatorExperiment(self.exp_2)
        next_views = exp_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 0)

    def _test_resource_navigation(self):

        # Test get next resource of resource 1 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_1)
        next_resources = resource_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 2)
        # Resource 2 of exp 1
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_1_resource_2.id]))
        # Resource 1 of exp 2
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_2_resource_1.id]))

        # Test get next resource of resource 2 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_2)
        next_resources = resource_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 1)
        # Resource 2 of exp 2
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_2_resource_2.id]))

        # Test previous resources of resource 1 exp 2
        resource_nav = EntityNavigatorResource(self.exp_2_resource_1)
        prev_resources = resource_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        # Resource 1 of exp 1
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_1.id]))

        # Test previous resources of resource 2 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_2)
        prev_resources = resource_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        # Resource 1 of exp 1
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_1.id]))

        # Test next views of resource 1 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_1)
        next_views = resource_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 1)
        # View 1 of resource 1 exp 1
        self.assertIsNotNone(len([x for x in next_views if x.id == self.exp_1_resource_1_view_1.id]))

        # Test next views of resource 2 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_2)
        next_views = resource_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 0)

        # Test next report of resource 1 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_1)
        next_reports = resource_nav.get_next_reports().get_entities_list()
        self.assertEqual(len(next_reports), 1)
        # Report 1
        self.assertIsNotNone(len([x for x in next_reports if x.id == self.report_1.id]))

        # Test next report of resource 2 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_2)
        next_reports = resource_nav.get_next_reports().get_entities_list()
        self.assertEqual(len(next_reports), 0)

    def _test_view_navigation(self):
        view_nav = EntityNavigatorView(self.exp_1_resource_1_view_1)

        # Test next report of view 1
        next_reports = view_nav.get_next_reports().get_entities_list()
        self.assertEqual(len(next_reports), 1)
        self.assertIsNotNone(len([x for x in next_reports if x.id == self.report_1.id]))

        # Test get previous resources of view 1
        prev_resources = view_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_1.id]))

        # Test get previous experiment of view 1
        prev_exps = view_nav.get_previous_experiments().get_entities_list()
        self.assertEqual(len(prev_exps), 1)
        self.assertIsNotNone(len([x for x in prev_exps if x.id == self.exp_1.id]))

    def _test_report_navigation(self):

        report_nav = EntityNavigatorReport(self.report_1)

        # Test get previous experiment of report 1
        prev_exps = report_nav.get_previous_experiments().get_entities_list()
        self.assertEqual(len(prev_exps), 1)
        self.assertIsNotNone(len([x for x in prev_exps if x.id == self.exp_1.id]))

        # Test get previous view of report 1
        prev_views = report_nav.get_previous_views().get_entities_list()
        self.assertEqual(len(prev_views), 1)
        self.assertIsNotNone(len([x for x in prev_views if x.id == self.exp_1_resource_1_view_1.id]))

        # Test get previous resource of report 1
        prev_resources = report_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_1.id]))

    def _test_recursive_navigation(self):

        exp = EntityNavigatorExperiment(self.exp_1)

        # Test get next entities of experiment 1
        next_exps = list(exp.get_next_entities_recursive())

        # return everything
        self.assertEqual(len(next_exps), 9)

        # Test get next entities of experiment 2
        exp = EntityNavigatorExperiment(self.exp_2)
        next_exps = list(exp.get_next_entities_recursive())
        self.assertEqual(len(next_exps), 4)

        # Test previous entities of experiment 3
        exp = EntityNavigatorExperiment(self.exp_3)
        prev_exps = list(exp.get_previous_entities_recursive())
        self.assertEqual(len(prev_exps), 5)

        # Test previous entities of experiment 2
        exp = EntityNavigatorExperiment(self.exp_2)
        prev_exps = list(exp.get_previous_entities_recursive())
        self.assertEqual(len(prev_exps), 3)
