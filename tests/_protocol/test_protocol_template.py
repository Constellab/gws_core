# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.core.classes.paginator import Paginator
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.protocol_template.protocol_template import ProtocolTemplate
from gws_core.protocol_template.protocol_template_service import \
    ProtocolTemplateService
from gws_core.task.task_model import TaskModel
from gws_core.test.base_test_case import BaseTestCase
from tests.protocol_examples import TestNestedProtocol


# test_protocol_template
class TestProtocolTemplate(BaseTestCase):

    def test_protocol_template(self):

        # create a chain
        proto: ProtocolModel = ProtocolService.create_protocol_model_from_type(
            TestNestedProtocol)

        # configure the process to check config in template
        ProtocolService.configure_process(proto.id, 'p5', {'food_weight': 1000})

        # configure the layout to check layout in template
        ProtocolService.save_process_layout(proto.id, 'p5', {'x': 1000, 'y': 1000})

        count_protocol = ProtocolModel.select().count()
        count_task = TaskModel.select().count()

        # create a template
        template: ProtocolTemplate = ProtocolService.create_protocol_template_from_id(
            protocol_id=proto.id, name='test_protocol_template')

        # get the template
        template_db: ProtocolTemplate = ProtocolTemplateService.get_by_id_and_check(template.id)

        self.assertEqual(template_db.name, 'test_protocol_template')
        self.assertIsNotNone(template_db.get_template()['nodes'])
        # check the sub protocol is in the template
        self.assertIsNotNone(template_db.get_template()['nodes']['mini_proto']['graph'])
        self.assertIsNotNone(template_db.get_template()['links'])
        self.assertIsNotNone(template_db.get_template()['layout'])
        self.assertIsInstance(template_db.to_json(deep=True), dict)

        # update the template
        ProtocolTemplateService.update(id=template.id, name='new_name')

        # get the template
        template_db = template_db.refresh()
        self.assertEqual(template_db.name, 'new_name')

        # test search
        paginator: Paginator = ProtocolTemplateService.search_by_name('ew_na')
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, template_db.id)

        # Test create an experiment from a template
        experiment = ExperimentService.create_experiment(protocol_template_id=template_db.id)

        # check that protocol and task are created
        self.assertEqual(ProtocolModel.select().count(), count_protocol * 2)
        self.assertEqual(TaskModel.select().count(), count_task * 2)

        # get check of created protocol and task, connector,  interface,
        # outerface, config and layout
        main_proto: ProtocolModel = experiment.protocol_model
        self.assertEqual(len(main_proto.connectors), 2)
        # check config
        self.assertEqual(main_proto.get_process('p5').config.get_value('food_weight'), 1000.0)
        # check layout
        self.assert_json(main_proto.layout.process_layouts['p5'], {'x': 1000, 'y': 1000})

        mini_proto: ProtocolModel = main_proto.get_process('mini_proto')
        self.assertIsNotNone(mini_proto)
        self.assertIsInstance(mini_proto, ProtocolModel)
        self.assertTrue(mini_proto.is_interfaced_with('p1'))
        self.assertTrue(mini_proto.is_outerfaced_with('p2'))
        p1 = mini_proto.get_process('p1')
        self.assertIsNotNone(p1)
        self.assertIsInstance(p1, TaskModel)

        # delete the template
        ProtocolTemplateService.delete(template.id)

        # check that the template is deleted
        with self.assertRaises(Exception):
            ProtocolTemplateService.get_by_id_and_check(template.id)
