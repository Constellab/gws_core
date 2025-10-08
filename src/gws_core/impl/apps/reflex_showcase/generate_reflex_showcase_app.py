
import os

from gws_core.apps.app_config import AppConfig, app_decorator
from gws_core.apps.app_dto import AppType
from gws_core.apps.reflex.reflex_resource import ReflexResource
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@app_decorator("ReflexShowcaseApp", app_type=AppType.REFLEX,
               human_name="Generate reflex showcase app")
class ReflexShowcaseApp(AppConfig):

    # retrieve the path of the app folder, relative to this file
    # the dashboard code folder starts with a underscore to avoid being loaded when the brick is loaded
    def get_app_folder_path(self):
        return self.get_app_folder_from_relative_path(
            __file__,
            "_reflex_showcase_app"
        )

    def get_dev_config_json_path(self) -> str:
        """Get the path to the dev config json file.

        :return: path to the dev config json file
        :rtype: str
        """
        return os.path.join(self.get_app_folder_path(), 'dev_config.json')

#     def get_shell_proxy(self) -> ShellProxy:
#         return MambaShellProxy.from_env_str("""
# name: my_test_env
# channels:
#   - conda-forge
# dependencies:
#   - pip
#   - pip:
#     - reflex==0.7.14
# """)


@task_decorator("GenerateReflexShowcaseApp", human_name="Generate reflex showcase app",
                short_description="App that showcases Constellab components for reflex",
                style=ReflexResource.copy_style())
class GenerateReflexShowcaseApp(Task):
    """
    Task that generates the reflex showcase app.

    This app showcases the reflex component developped by Gencovery to simplify
    the creation of reflex apps.

    Some components are generic reflex components (like containers), other wrap Constellab UI components.
    """

    input_specs = InputSpecs({
        'resource': InputSpec(Resource, optional=True)
    })

    output_specs = OutputSpecs({
        'reflex_app': OutputSpec(ReflexResource)
    })

    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        reflex_app = ReflexResource()

        resource = inputs.get('resource', None)
        if resource is not None:
            reflex_app.add_resource(resource, create_new_resource=False)

        reflex_app.set_app_config(ReflexShowcaseApp())
        reflex_app.set_requires_authentication(False)
        reflex_app.set_name("Reflex Showcase App")

        return {"reflex_app": reflex_app}
