from gws_core.config.param.param_spec import IntParam
from gws_core.impl.agent.py_agent import PyAgent
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.test.base_test_case import BaseTestCase


class TestDynamicParam(BaseTestCase):

    def test(self):

        proto: ProtocolModel = ProtocolService.create_empty_protocol()

        process_model = ProtocolService.add_process_to_protocol_id(
            proto.id,
            PyAgent.get_typing_name(),
            'task'
        ).process

        proto = proto.refresh()

        ProtocolService.add_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, 'params', 'a', IntParam(default_value=2).to_dto()
        )

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)
        self.assertIsNotNone(test_process_model.config.get_spec(PyAgent.CONFIG_PARAMS_NAME).specs['a'])
        self.assertIsNotNone(test_process_model.config.get_value('params'))
        self.assertEqual(test_process_model.config.get_spec('params').specs['a'].to_dto()
                         .to_json_dict(), IntParam(default_value=2).to_dto().to_json_dict())
        self.assertEqual(test_process_model.config.get_value('params')['a'], 2)

        process_model: ProcessModel = proto.get_process('task')

        ProtocolService.update_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, 'params', 'a', IntParam(default_value=3).to_dto()
        )

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)
        self.assertIsNotNone(test_process_model.config.get_spec('params').specs['a'])
        self.assertIsNotNone(test_process_model.config.get_value('params'))
        self.assertEqual(test_process_model.config.get_spec('params')
                         .specs['a'].to_dto().to_json_dict(), IntParam(default_value=3).to_dto().to_json_dict())
        self.assertEqual(test_process_model.config.get_value('params')['a'], 3)

        process_model: ProcessModel = proto.get_process('task')

        ProtocolService.rename_and_update_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, 'params', 'a', 'b', IntParam(default_value=4).to_dto()
        )

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)
        self.assertIsNotNone(test_process_model.config.get_spec('params').specs['b'])
        self.assertTrue('a' not in test_process_model.config.get_spec('params').specs)
        self.assertIsNotNone(test_process_model.config.get_value('params'))
        self.assertEqual(test_process_model.config.get_spec('params')
                         .specs['b'].to_dto().to_json_dict(), IntParam(default_value=4).to_dto().to_json_dict())
        self.assertEqual(test_process_model.config.get_value('params')['b'], 4)
        self.assertTrue('a' not in test_process_model.config.get_values())

        process_model: ProcessModel = proto.get_process('task')

        ProtocolService.remove_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, 'params', 'b'
        )

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)
        self.assertTrue('a' not in test_process_model.config.get_spec('params').specs)
        self.assertTrue('a' not in test_process_model.config.get_value('params'))
