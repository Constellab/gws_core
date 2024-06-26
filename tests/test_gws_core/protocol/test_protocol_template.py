

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.experiment.experiment_dto import ExperimentSaveDTO
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.protocol_template.protocol_template_service import \
    ProtocolTemplateService
from gws_core.resource.resource import Resource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs
from gws_core.task.task_model import TaskModel
from gws_core.test.base_test_case import BaseTestCase

from ..protocol_examples import TestNestedProtocol


@task_decorator("TestProtocolTemplateDynamic")
class TestProtocolTemplateDynamic(Task):

    input_specs: InputSpecs = DynamicInputs()
    output_specs: OutputSpecs = DynamicOutputs()
    config_specs: ConfigSpecs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {}


@task_decorator("TestGenerator")
class TestGenerator(Task):

    output_specs: OutputSpecs = OutputSpecs({'resource': OutputSpec(Resource)})
    config_specs: ConfigSpecs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {}


# test_protocol_template
class TestProtocolTemplate(BaseTestCase):

    def test_protocol_template(self):

        init_count_protocol = ProtocolModel.select().count()
        init_count_task = TaskModel.select().count()

        # create a chain
        proto = ProtocolService.create_protocol_model_from_type(
            TestNestedProtocol)

        # configure the process to check config in template
        ProtocolService.configure_process(proto.id, 'p5', {'food_weight': 1000})

        # configure the layout to check layout in template
        ProtocolService.save_process_layout(proto.id, 'p5', {'x': 1000, 'y': 1000})

        count_protocol = ProtocolModel.select().count() - init_count_protocol
        count_task = TaskModel.select().count() - init_count_task

        # create a template
        template = ProtocolService.create_protocol_template_from_id(
            protocol_id=proto.id, name='test_protocol_template')

        # get the template
        template_db = ProtocolTemplateService.get_by_id_and_check(template.id)

        self.assertEqual(template_db.name, 'test_protocol_template')
        self.assertIsNotNone(template_db.get_template().nodes)
        # check the sub protocol is in the template
        self.assertIsNotNone(template_db.get_template().nodes['mini_proto'].graph)
        self.assertIsNotNone(template_db.get_template().links)
        self.assertIsNotNone(template_db.get_template().layout)
        self.assertIsNotNone(template_db.to_export_dto())
        self.assertIsNotNone(template_db.get_protocol_config_dto())

        # update the template
        ProtocolTemplateService.update(id=template.id, name='new_name')

        # get the template
        template_db = template_db.refresh()
        self.assertEqual(template_db.name, 'new_name')

        # test search
        paginator = ProtocolTemplateService.search_by_name('ew_na')
        self.assertEqual(paginator.page_info.total_number_of_items, 1)
        self.assertEqual(paginator.results[0].id, template_db.id)

        # Test create an experiment from a template
        experiment = ExperimentService.create_experiment(protocol_template=template_db)

        # check that protocol and task are created
        self.assertEqual(ProtocolModel.select().count(), init_count_protocol + (count_protocol * 2))
        self.assertEqual(TaskModel.select().count(), init_count_task + (count_task * 2))

        # get check of created protocol and task, connector,  interface,
        # outerface, config and layout
        main_proto = experiment.protocol_model
        self.assertEqual(len(main_proto.connectors), 2)
        # check config
        self.assertEqual(main_proto.get_process('p5').config.get_value('food_weight'), 1000.0)
        # check layout
        self.assert_json(main_proto.layout.process_layouts['p5'].to_json_dict(), {'x': 1000, 'y': 1000})

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

    def test_dynamic_io(self):
        """ Test that the protocol template supports dynamic io"""
        experiment = IExperiment()

        protocol = experiment.get_protocol()

        process = protocol.add_process(TestProtocolTemplateDynamic, 'dynamic')
        source_1 = protocol.add_process(TestGenerator, 'source_1')
        source_2 = protocol.add_process(TestGenerator, 'source_2')

        ProtocolService.add_dynamic_input_port_to_process(protocol.get_model().id, process.get_model().instance_name)
        ProtocolService.add_dynamic_output_port_to_process(protocol.get_model().id, process.get_model().instance_name)

        protocol.refresh()
        process.refresh()

        # connect all dynamic input to a source
        keys = list(process.get_model().inputs.ports.keys())
        protocol.add_connector(source_1 >> 'resource', process << keys[0])
        protocol.add_connector(source_2 >> 'resource', process << keys[1])

        # connect all dynamic output to a sink
        i = 0
        for output_port in process.get_model().outputs.ports.keys():
            protocol.add_sink(f'target_{i}', process >> output_port)
            i += 1

        # create a template
        template = ProtocolService.create_protocol_template_from_id(
            protocol_id=protocol.get_model().id, name='test_dynamic')

        # Test create an experiment from a template
        experiment_dto = ExperimentSaveDTO(protocol_template_id=template.id, title='')
        experiment = ExperimentService.create_experiment_from_dto(experiment_dto)

        # check that protocol and task are created
        protocol_2 = experiment.protocol_model
        self.assertEqual(len(protocol_2.processes), 5)
        self.assertEqual(len(protocol_2.connectors), 4)

        # Test create the same experiment with the template json instead of the template id
        export_dto = template.to_export_dto()
        experiment_dto = ExperimentSaveDTO(protocol_template_json=export_dto.to_json_dict(), title='')
        experiment = ExperimentService.create_experiment_from_dto(experiment_dto)

        # check that protocol and task are created
        protocol_3 = experiment.protocol_model
        self.assertEqual(len(protocol_3.processes), 5)
        self.assertEqual(len(protocol_3.connectors), 4)
