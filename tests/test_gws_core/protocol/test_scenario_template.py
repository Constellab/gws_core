from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.impl.robot.robot_tasks import RobotMove
from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.resource.resource import Resource
from gws_core.scenario.scenario_dto import ScenarioSaveDTO
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.scenario_template.scenario_template_factory import ScenarioTemplateFactory
from gws_core.scenario_template.scenario_template_service import ScenarioTemplateService
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.task.task_model import TaskModel
from gws_core.test.base_test_case import BaseTestCase

from ..protocol_examples import TestNestedProtocol


@task_decorator("TestScenarioTemplateDynamic")
class TestScenarioTemplateDynamic(Task):
    input_specs: InputSpecs = DynamicInputs()
    output_specs: OutputSpecs = DynamicOutputs()
    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {}


@task_decorator("TestGenerator")
class TestGenerator(Task):
    output_specs: OutputSpecs = OutputSpecs({"resource": OutputSpec(Resource)})
    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {}


# test_scenario_template
class TestScenarioTemplate(BaseTestCase):
    def test_scenario_template(self):
        init_count_protocol = ProtocolModel.select().count()
        init_count_task = TaskModel.select().count()

        # create a chain
        proto = ProtocolService.create_protocol_model_from_type(TestNestedProtocol)

        # configure the process to check config in template
        ProtocolService.configure_process(proto.id, "p5", {"food_weight": 1000})

        # configure the layout to check layout in template
        ProtocolService.save_process_layout(proto.id, "p5", {"x": 1000, "y": 1000})

        count_protocol = ProtocolModel.select().count() - init_count_protocol
        count_task = TaskModel.select().count() - init_count_task

        # create a template
        template = ProtocolService.create_scenario_template_from_id(
            protocol_id=proto.id, name="test_scenario_template"
        )

        # get the template
        template_db = ScenarioTemplateService.get_by_id_and_check(template.id)

        self.assertEqual(template_db.name, "test_scenario_template")
        self.assertIsNotNone(template_db.get_template().nodes)
        # check the sub protocol is in the template
        self.assertIsNotNone(template_db.get_template().nodes["mini_proto"].graph)
        self.assertIsNotNone(template_db.get_template().links)
        self.assertIsNotNone(template_db.get_template().layout)
        self.assertIsNotNone(template_db.to_export_dto())
        self.assertIsNotNone(template_db.get_protocol_config_dto())

        # update the template
        ScenarioTemplateService.update(id_=template.id, name="new_name")

        # get the template
        template_db = template_db.refresh()
        self.assertEqual(template_db.name, "new_name")

        # test search
        paginator = ScenarioTemplateService.search_by_name("ew_na")
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, template_db.id)

        # Test create a scenario from a template
        scenario = ScenarioService.create_scenario(scenario_template=template_db)

        # check that protocol and task are created
        self.assertEqual(ProtocolModel.select().count(), init_count_protocol + (count_protocol * 2))
        self.assertEqual(TaskModel.select().count(), init_count_task + (count_task * 2))

        # get check of created protocol and task, connector,  interface,
        # outerface, config and layout
        main_proto = scenario.protocol_model
        self.assertEqual(len(main_proto.connectors), 2)
        # check config
        self.assertEqual(main_proto.get_process("p5").config.get_value("food_weight"), 1000.0)
        # check layout
        self.assert_json(
            main_proto.layout.process_layouts["p5"].to_json_dict(), {"x": 1000, "y": 1000}
        )

        mini_proto: ProtocolModel = main_proto.get_process("mini_proto")
        self.assertIsNotNone(mini_proto)
        self.assertIsInstance(mini_proto, ProtocolModel)
        self.assertTrue(mini_proto.is_interfaced_with("p1"))
        self.assertTrue(mini_proto.is_outerfaced_with("p2"))
        p1 = mini_proto.get_process("p1")
        self.assertIsNotNone(p1)
        self.assertIsInstance(p1, TaskModel)

        # delete the template
        ScenarioTemplateService.delete(template.id)

        # check that the template is deleted
        with self.assertRaises(Exception):
            ScenarioTemplateService.get_by_id_and_check(template.id)

    def test_dynamic_io(self):
        """Test that the component supports dynamic io"""
        scenario = ScenarioProxy()

        protocol = scenario.get_protocol()

        process = protocol.add_process(TestScenarioTemplateDynamic, "dynamic")
        source_1 = protocol.add_process(TestGenerator, "source_1")
        source_2 = protocol.add_process(TestGenerator, "source_2")

        ProtocolService.add_dynamic_input_port_to_process(
            protocol.get_model().id, process.get_model().instance_name
        )
        ProtocolService.add_dynamic_output_port_to_process(
            protocol.get_model().id, process.get_model().instance_name
        )

        protocol.refresh()
        process.refresh()

        # connect all dynamic input to a source
        keys = list(process.get_model().inputs.ports.keys())
        protocol.add_connector(source_1 >> "resource", process << keys[0])
        protocol.add_connector(source_2 >> "resource", process << keys[1])

        # connect all dynamic output to a output
        i = 0
        for output_port in process.get_model().outputs.ports.keys():
            protocol.add_output(f"target_{i}", process >> output_port)
            i += 1

        # create a template
        template = ProtocolService.create_scenario_template_from_id(
            protocol_id=protocol.get_model().id, name="test_dynamic"
        )

        # Test create a scenario from a template
        scenario_dto = ScenarioSaveDTO(scenario_template_id=template.id, title="")
        scenario = ScenarioService.create_scenario_from_dto(scenario_dto)

        # check that protocol and task are created
        protocol_2 = scenario.protocol_model
        self.assertEqual(len(protocol_2.processes), 5)
        self.assertEqual(len(protocol_2.connectors), 4)

        # Test create the same scenario with the template json instead of the template id
        export_dto = template.to_export_dto()
        scenario_dto = ScenarioSaveDTO(scenario_template_json=export_dto.to_json_dict(), title="")
        scenario = ScenarioService.create_scenario_from_dto(scenario_dto)

        # check that protocol and task are created
        protocol_3 = scenario.protocol_model
        self.assertEqual(len(protocol_3.processes), 5)
        self.assertEqual(len(protocol_3.connectors), 4)

    def test_serialization(self):
        # create a chain
        proto = ProtocolService.create_protocol_model_from_type(TestNestedProtocol)

        # create a template
        template = ProtocolService.create_scenario_template_from_id(
            protocol_id=proto.id, name="test_scenario_template"
        )

        template_str = template.to_export_dto().to_json_str()
        new_template = ScenarioTemplateFactory.from_export_dto_str(template_str)
        self.assert_json(new_template.name, template.name)
        self.assert_json(new_template.version, template.version)
        self.assert_json(new_template.description, template.description)
        self.assert_json(
            new_template.to_export_dto().data.to_json_dict(),
            template.to_export_dto().data.to_json_dict(),
            ["id"],
        )

    def test_add_scenario_component_to_protocol(self):
        i_scenario = ScenarioProxy()

        protocol = i_scenario.get_protocol()

        process = protocol.add_process(RobotMove, "robotMove")
        protocol.add_resource("source", None, process << "robot")
        protocol.add_output("output", process >> "robot")

        # create scenario template
        template = ProtocolService.create_scenario_template_from_id(
            protocol.get_model().id, "test_template"
        )

        # Create an empty scenario
        scenario_2 = ScenarioProxy()

        # Add the scenario template to the scenario
        protocol_model_2 = scenario_2.get_protocol().get_model()
        protocol_update = ProtocolService.add_scenario_template_to_protocol(
            protocol_model_2.id, template.id
        )

        # Check that the component is added to the protocol
        protocol_2: ProtocolProxy = scenario_2.get_protocol().refresh()
        sub_protocol: ProtocolModel = protocol_2.get_process(
            protocol_update.process.instance_name
        ).get_model()

        self.assertIsInstance(sub_protocol, ProtocolModel)
        self.assertEqual(sub_protocol.name, "test_template")
        self.assertEqual(len(sub_protocol.inputs.ports), 1)
        self.assertEqual(len(sub_protocol.outputs.ports), 1)
        self.assertEqual(len(sub_protocol.interfaces), 1)
        self.assertEqual(len(sub_protocol.outerfaces), 1)
        self.assertEqual(len(sub_protocol.processes), 1)
        sub_process = sub_protocol.get_process("robotMove")
        self.assertIsNotNone(sub_process)
        self.assertEqual(sub_process.get_process_type(), RobotMove)

    def test_migration(self):
        # Simple protocol Input > TableTransposer on v1
        old_scenario_template = {
            "id": "123",
            "version": 1,
            "name": "test",
            "description": None,
            "data": {
                "nodes": {
                    "TableTransposer": {
                        "process_typing_name": "TASK.gws_core.TableTransposer",
                        "instance_name": "TableTransposer",
                        "config": {"specs": {}, "values": {}},
                        "brick_version": "0.4.5",
                        "inputs": {
                            "ports": {
                                "source": {
                                    "resource_id": "9a9f94d8-091d-406e-ad1e-fd5c3da3efda",
                                    "specs": {
                                        "resource_types": [
                                            {
                                                "typing_name": "RESOURCE.gws_core.Table",
                                                "brick_version": "0.5.11",
                                                "human_name": "Table",
                                            }
                                        ],
                                        "optional": False,
                                        "human_name": "Table",
                                        "short_description": "2d excel like table",
                                    },
                                }
                            },
                            "type": "normal",
                            "additional_info": {},
                        },
                        "outputs": {
                            "ports": {
                                "target": {
                                    "resource_id": "6d566157-d472-4d0d-bbf4-e34a281cfb3b",
                                    "specs": {
                                        "resource_types": [
                                            {
                                                "typing_name": "RESOURCE.gws_core.Table",
                                                "brick_version": "0.5.11",
                                                "human_name": "Table",
                                            }
                                        ],
                                        "optional": False,
                                        "human_name": "Table",
                                        "short_description": "2d excel like table",
                                        "sub_class": False,
                                        "constant": False,
                                    },
                                }
                            },
                            "type": "normal",
                            "additional_info": {},
                        },
                        "status": "SUCCESS",
                        "name": "Table transposer",
                        "process_type": {
                            "human_name": "Table transposer",
                            "short_description": "Transposes the table",
                        },
                    },
                    "input_1": {
                        "process_typing_name": "TASK.gws_core.InputTask",
                        "instance_name": "input_1",
                        "config": {
                            "specs": {
                                "resource_id": {
                                    "type": "str",
                                    "optional": True,
                                    "visibility": "public",
                                    "additional_info": {"min_length": None, "max_length": None},
                                    "short_description": "The id of the resource",
                                }
                            },
                            "values": {"resource_id": "9a9f94d8-091d-406e-ad1e-fd5c3da3efda"},
                        },
                        "brick_version": "0.4.5",
                        "inputs": {"ports": {}, "type": "normal", "additional_info": {}},
                        "outputs": {
                            "ports": {
                                "resource": {
                                    "resource_id": "9a9f94d8-091d-406e-ad1e-fd5c3da3efda",
                                    "specs": {
                                        "resource_types": [
                                            {
                                                "typing_name": "RESOURCE.gws_core.Resource",
                                                "brick_version": "0.5.11",
                                                "human_name": "Resource",
                                            }
                                        ],
                                        "optional": False,
                                        "human_name": "Resource",
                                        "short_description": "Loaded resource",
                                        "sub_class": True,
                                        "constant": True,
                                    },
                                }
                            },
                            "type": "normal",
                            "additional_info": {},
                        },
                        "status": "SUCCESS",
                        "name": "Input",
                        "process_type": {"human_name": "Input", "short_description": ""},
                    },
                },
                "links": [
                    {
                        "from": {"node": "input_1", "port": "resource"},
                        "to": {"node": "TableTransposer", "port": "source"},
                    }
                ],
                "interfaces": {},
                "outerfaces": {},
                "layout": {
                    "process_layouts": {
                        "TableTransposer": {"x": 348, "y": 125},
                        "input_1": {"x": 62, "y": 105},
                    },
                    "interface_layouts": {},
                    "outerface_layouts": {},
                },
            },
        }

        new_scenario_template = ScenarioTemplateFactory.from_export_dto_dict(old_scenario_template)
        self.assertEqual(new_scenario_template.version, 3)
