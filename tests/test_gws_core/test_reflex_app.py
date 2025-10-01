

from typing import cast

from pandas import DataFrame

from gws_core.apps.app_dto import AppProcessStatus
from gws_core.apps.apps_manager import AppsManager
from gws_core.apps.reflex.reflex_process import ReflexProcess
from gws_core.apps.reflex.reflex_resource import ReflexResource
from gws_core.config.config_params import ConfigParams
from gws_core.impl.apps.reflex_showcase.generate_reflex_showcase_app import \
    GenerateReflexShowcaseApp
from gws_core.impl.table.table import Table
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.test.base_test_case import BaseTestCase


# test_reflex_app
class TestReflexApp(BaseTestCase):

    def test_reflex_resource(self):
        df = DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        table = Table(df)

        resource_model = ResourceModel.save_from_resource(table, origin=ResourceOrigin.UPLOADED)

        scenario_proxy = ScenarioProxy()
        protocol_proxy = scenario_proxy.get_protocol()
        generate_task = protocol_proxy.add_task(GenerateReflexShowcaseApp, 'generate')
        protocol_proxy.add_source('resource', resource_model.id, generate_task.get_input_port('resource'))

        scenario_proxy.run()

        generate_task = generate_task.refresh()

        reflex_resource = cast(ReflexResource, generate_task.get_output('reflex_app'))
        # make the check faster to avoid test block
        ReflexProcess.CHECK_RUNNING_INTERVAL = 3

        try:
            # generate the reflex app
            reflex_resource.default_view(ConfigParams())

            reflex_process = AppsManager.find_process_of_app(reflex_resource.get_model_id())

            if reflex_process is None:
                self.fail("No reflex process found")

            reflex_process.wait_for_start()
            if not reflex_process.is_running():
                self.fail("Reflex process is not running")

            # check if the app is running
            self.assertTrue(reflex_process.call_health_check())

            status = reflex_process.get_status_dto()
            self.assertEqual(status.status, AppProcessStatus.RUNNING)
            self.assertEqual(len(status.running_apps), 1)
            self.assertEqual(status.running_apps[0].app_resource_id, reflex_resource.get_model_id())

            AppsManager.stop_all_processes()

            # check if the app is running
            self.assertFalse(reflex_process.call_health_check())
            self.assertFalse(reflex_process.subprocess_is_running())
        finally:
            AppsManager.stop_all_processes()
