from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.scenario.scenario_enums import ScenarioCreationType, ScenarioStatus
from gws_core.scenario.scenario_loader import ScenarioLoader
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.scenario.scenario_zipper import ScenarioExportPackage
from gws_core.test.base_test_case import BaseTestCase


# test_scenario_zipper_loader
class TestScenarioZipperLoader(BaseTestCase):
    def test_export_and_load_scenario(self):
        """Test exporting a scenario with processes, running it, then loading it via ScenarioLoader."""
        # Create a scenario RobotCreate > RobotMove
        scenario = ScenarioProxy(title="Export test scenario")
        protocol = scenario.get_protocol()
        create = protocol.add_process(RobotCreate, "create")
        move = protocol.add_process(RobotMove, "move")
        protocol.add_connector(create >> "robot", move << "robot")

        # Run the scenario to generate resources
        scenario.run()
        scenario.refresh()
        scenario_model = scenario.get_model()
        self.assertEqual(scenario_model.status, ScenarioStatus.SUCCESS)

        # Export the scenario
        export_package = ScenarioService.export_scenario(scenario_model.id)

        # Verify export package structure
        self.assertIsInstance(export_package, ScenarioExportPackage)
        self.assertEqual(export_package.zip_version, 1)
        self.assertEqual(export_package.scenario.id, scenario_model.id)
        self.assertEqual(export_package.scenario.title, "Export test scenario")
        self.assertEqual(export_package.scenario.status, ScenarioStatus.SUCCESS)
        self.assertEqual(export_package.protocol.version, 3)
        self.assertIsNotNone(export_package.protocol.data)
        self.assertGreater(len(export_package.main_resource_models), 0)

        # Load the exported scenario
        loader = ScenarioLoader(export_package)
        loaded_scenario = loader.load_scenario()

        # Verify loaded scenario metadata
        self.assertEqual(loaded_scenario.id, scenario_model.id)
        self.assertEqual(loaded_scenario.title, "Export test scenario")
        self.assertEqual(loaded_scenario.status, ScenarioStatus.SUCCESS)
        self.assertEqual(loaded_scenario.creation_type, ScenarioCreationType.IMPORTED)

        # Verify protocol processes and connectors are preserved
        protocol_model = loader.get_protocol_model()
        self.assertEqual(len(protocol_model.processes), 2)
        self.assertIsNotNone(protocol_model.get_process("create"))
        self.assertIsNotNone(protocol_model.get_process("move"))
        self.assertEqual(len(protocol_model.connectors), 1)

        # Verify process IDs are preserved
        original_protocol = scenario_model.protocol_model
        for instance_name in ["create", "move"]:
            original_process = original_protocol.get_process(instance_name)
            loaded_process = protocol_model.get_process(instance_name)
            self.assertEqual(loaded_process.id, original_process.id)

        # Verify tags (none set, should be empty)
        tags = loader.get_tags()
        self.assertEqual(len(tags), 0)
