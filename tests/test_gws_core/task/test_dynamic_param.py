from gws_core.config.param.dynamic_param import DynamicParam
from gws_core.config.param.param_spec import IntParam
from gws_core.impl.agent.py_agent import PyAgent
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.test.base_test_case import BaseTestCase


# test_dynamic_param
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
            proto.id, process_model.instance_name, PyAgent.CONFIG_PARAMS_NAME, 'a',
            IntParam(default_value=2, optional=True).to_dto())

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)

        dynamic_param: DynamicParam = test_process_model.config.get_spec(PyAgent.CONFIG_PARAMS_NAME)
        self.assertIsInstance(dynamic_param, DynamicParam)

        int_param: IntParam = dynamic_param.specs.get_spec('a')
        self.assertIsNotNone(int_param)

        self.assertIsNotNone(test_process_model.config.get_value(PyAgent.CONFIG_PARAMS_NAME))
        self.assertEqual(int_param.to_dto().to_json_dict(), IntParam(
            default_value=2, optional=True).to_dto().to_json_dict())
        self.assertEqual(test_process_model.config.get_value(PyAgent.CONFIG_PARAMS_NAME)['a'], 2)

        process_model = proto.get_process('task')

        ProtocolService.update_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, PyAgent.CONFIG_PARAMS_NAME, 'a', IntParam(default_value=3).to_dto()
        )

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)

        int_param = test_process_model.config.get_spec(PyAgent.CONFIG_PARAMS_NAME).specs.get_spec('a')
        self.assertIsNotNone(int_param)
        self.assertIsNotNone(test_process_model.config.get_value(PyAgent.CONFIG_PARAMS_NAME))
        self.assertEqual(int_param.to_dto().to_json_dict(), IntParam(
            default_value=3, optional=True).to_dto().to_json_dict())

        process_model = proto.get_process('task')

        ProtocolService.rename_and_update_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, PyAgent.CONFIG_PARAMS_NAME, 'a', 'b',
            IntParam(default_value=4, optional=True).to_dto())

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)

        dynamic_param = test_process_model.config.get_spec(PyAgent.CONFIG_PARAMS_NAME)
        int_param = dynamic_param.specs.get_spec('b')

        self.assertFalse(dynamic_param.specs.has_spec('a'))
        self.assertIsNotNone(int_param)
        self.assertIsNotNone(test_process_model.config.get_value(PyAgent.CONFIG_PARAMS_NAME))
        self.assertEqual(int_param.to_dto().to_json_dict(), IntParam(
            default_value=4, optional=True).to_dto().to_json_dict())
        self.assertTrue('a' not in test_process_model.config.get_values())

        process_model = proto.get_process('task')

        ProtocolService.remove_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, PyAgent.CONFIG_PARAMS_NAME, 'b'
        )

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)
        self.assertFalse(test_process_model.config.get_spec(PyAgent.CONFIG_PARAMS_NAME).specs.has_spec('b'))
        self.assertTrue('b' not in test_process_model.config.get_value(PyAgent.CONFIG_PARAMS_NAME))
