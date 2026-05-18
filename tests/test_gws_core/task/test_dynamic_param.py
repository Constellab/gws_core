from gws_core.config.param.dynamic_param import DynamicParam
from gws_core.config.param.param_spec import IntParam
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.impl.agent.py_agent import PyAgent
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.test.base_test_case import BaseTestCase


# test_dynamic_param
class TestDynamicParam(BaseTestCase):
    def test(self):
        proto: ProtocolModel = ProtocolService.create_empty_protocol()

        process_model = ProtocolService.add_process_to_protocol_id(
            proto.id, PyAgent.get_typing_name(), "task"
        ).process

        proto = proto.refresh()

        ProtocolService.add_dynamic_param_spec_of_process(
            proto.id,
            process_model.instance_name,
            PyAgent.CONFIG_PARAMS_NAME,
            "a",
            IntParam(default_value=2, optional=True).to_dto(),
        )

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)

        dynamic_param: DynamicParam = test_process_model.config.get_spec(PyAgent.CONFIG_PARAMS_NAME)
        self.assertIsInstance(dynamic_param, DynamicParam)

        int_param: IntParam = dynamic_param.specs.get_spec("a")
        self.assertIsNotNone(int_param)

        self.assertIsNotNone(test_process_model.config.get_value(PyAgent.CONFIG_PARAMS_NAME))
        self.assertEqual(
            int_param.to_dto().to_json_dict(),
            IntParam(default_value=2, optional=True).to_dto().to_json_dict(),
        )
        self.assertEqual(test_process_model.config.get_value(PyAgent.CONFIG_PARAMS_NAME)["a"], 2)

        process_model = proto.get_process("task")

        ProtocolService.update_dynamic_param_spec_of_process(
            proto.id,
            process_model.instance_name,
            PyAgent.CONFIG_PARAMS_NAME,
            "a",
            IntParam(default_value=3).to_dto(),
        )

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)

        int_param = test_process_model.config.get_spec(PyAgent.CONFIG_PARAMS_NAME).specs.get_spec(
            "a"
        )
        self.assertIsNotNone(int_param)
        self.assertIsNotNone(test_process_model.config.get_value(PyAgent.CONFIG_PARAMS_NAME))
        self.assertEqual(
            int_param.to_dto().to_json_dict(),
            IntParam(default_value=3, optional=True).to_dto().to_json_dict(),
        )

        process_model = proto.get_process("task")

        ProtocolService.rename_and_update_dynamic_param_spec_of_process(
            proto.id,
            process_model.instance_name,
            PyAgent.CONFIG_PARAMS_NAME,
            "a",
            "b",
            IntParam(default_value=4, optional=True).to_dto(),
        )

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)

        dynamic_param = test_process_model.config.get_spec(PyAgent.CONFIG_PARAMS_NAME)
        int_param = dynamic_param.specs.get_spec("b")

        self.assertFalse(dynamic_param.specs.has_spec("a"))
        self.assertIsNotNone(int_param)
        self.assertIsNotNone(test_process_model.config.get_value(PyAgent.CONFIG_PARAMS_NAME))
        self.assertEqual(
            int_param.to_dto().to_json_dict(),
            IntParam(default_value=4, optional=True).to_dto().to_json_dict(),
        )
        self.assertTrue("a" not in test_process_model.config.get_values())

        process_model = proto.get_process("task")

        ProtocolService.remove_dynamic_param_spec_of_process(
            proto.id, process_model.instance_name, PyAgent.CONFIG_PARAMS_NAME, "b"
        )

        proto = proto.refresh()

        test_process_model = proto.get_process(process_model.instance_name)
        self.assertIsNotNone(test_process_model)
        self.assertFalse(
            test_process_model.config.get_spec(PyAgent.CONFIG_PARAMS_NAME).specs.has_spec("b")
        )
        self.assertTrue("b" not in test_process_model.config.get_value(PyAgent.CONFIG_PARAMS_NAME))

    def _setup_dynamic_params(self, names: list[str]) -> tuple[ProtocolModel, str]:
        """Create a protocol with a PyAgent process and the given dynamic params.

        Returns the protocol and the process instance name.
        """
        proto: ProtocolModel = ProtocolService.create_empty_protocol()
        process_model = ProtocolService.add_process_to_protocol_id(
            proto.id, PyAgent.get_typing_name(), "task"
        ).process
        for name in names:
            ProtocolService.add_dynamic_param_spec_of_process(
                proto.id,
                process_model.instance_name,
                PyAgent.CONFIG_PARAMS_NAME,
                name,
                IntParam(default_value=1, optional=True).to_dto(),
            )
        return proto.refresh(), process_model.instance_name

    def test_reorder_dynamic_param_specs(self):
        proto, instance_name = self._setup_dynamic_params(["a", "b", "c"])

        ProtocolService.reorder_dynamic_param_specs_of_process(
            proto.id, instance_name, PyAgent.CONFIG_PARAMS_NAME, ["c", "a", "b"]
        )

        proto = proto.refresh()
        dynamic_param: DynamicParam = proto.get_process(instance_name).config.get_spec(
            PyAgent.CONFIG_PARAMS_NAME
        )
        self.assertEqual(list(dynamic_param.specs.specs.keys()), ["c", "a", "b"])

    def test_reorder_rejects_mismatched_set(self):
        proto, instance_name = self._setup_dynamic_params(["a", "b"])

        # Missing a current name.
        with self.assertRaises(BadRequestException):
            ProtocolService.reorder_dynamic_param_specs_of_process(
                proto.id, instance_name, PyAgent.CONFIG_PARAMS_NAME, ["a"]
            )

        # Unknown name.
        with self.assertRaises(BadRequestException):
            ProtocolService.reorder_dynamic_param_specs_of_process(
                proto.id, instance_name, PyAgent.CONFIG_PARAMS_NAME, ["a", "b", "ghost"]
            )

    def test_reorder_rejects_duplicates(self):
        proto, instance_name = self._setup_dynamic_params(["a", "b"])

        with self.assertRaises(BadRequestException):
            ProtocolService.reorder_dynamic_param_specs_of_process(
                proto.id, instance_name, PyAgent.CONFIG_PARAMS_NAME, ["a", "a"]
            )
