

from pandas import DataFrame

from gws_core.apps.apps_manager import AppsManager
from gws_core.apps.reflex.reflex_process import ReflexProcess
from gws_core.apps.reflex.reflex_resource import ReflexResource
from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.settings import Settings
from gws_core.impl.apps.reflex_showcase.generate_reflex_showcase_app import \
    ReflexShowcaseApp
from gws_core.impl.table.table import Table
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.test.base_test_case import BaseTestCase


# test_reflex_app
class TestReflexApp(BaseTestCase):

    def test_reflex_resource(self):
        df = DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        table = Table(df)
        resource_model = ResourceModel.save_from_resource(table, origin=ResourceOrigin.UPLOADED)

        reflex_config = ReflexShowcaseApp()
        reflex_resource: ReflexResource = ReflexResource()
        reflex_resource.set_app_config(reflex_config)
        reflex_resource.add_resource(resource_model.get_resource())
        resource_model = ResourceModel.save_from_resource(
            reflex_resource,
            origin=ResourceOrigin.UPLOADED)

        reflex_resource = resource_model.get_resource()
        # make the check faster to avoid test block
        ReflexProcess.CHECK_RUNNING_INTERVAL = 3

        try:
            # generate the reflex app
            reflex_resource.default_view(ConfigParams())

            reflex_process: ReflexProcess = None
            for proc in AppsManager.running_processes.values():
                if proc.has_app(reflex_resource.get_model_id()):
                    if isinstance(proc, ReflexProcess):
                        reflex_process = proc
                    break

            if reflex_process is None:
                self.fail("No reflex process found")

            # check if the app is running
            self.assertTrue(reflex_process.call_health_check())

            status = reflex_process.get_status_dto()
            self.assertEqual(status.status, 'RUNNING')
            self.assertEqual(len(status.running_apps), 1)
            self.assertEqual(status.running_apps[0].app_resource_id, reflex_resource.get_model_id())

            self.assertEqual(reflex_process.front_port, Settings.get_app_ports()[0])
            self.assertEqual(reflex_process.back_port, Settings.get_app_ports()[1])

            AppsManager.stop_all_processes()

            # check if the app is running
            self.assertFalse(reflex_process.call_health_check())
            self.assertFalse(reflex_process.process_is_running())
        finally:
            AppsManager.stop_all_processes()
