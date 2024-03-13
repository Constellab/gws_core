

import importlib
import pathlib
import sys

from ...impl.shell.shell_proxy import ShellProxy
from .logger import Logger
from .string_helper import StringHelper


class PackageHelper:

    # @staticmethod
    # def is_installed(package) -> bool:
    #     output = subprocess.check_output([sys.executable, "-m", "pip", "list"])
    #     return package in output

    @staticmethod
    def module_exists(module_name=None) -> bool:
        return module_name in sys.modules

    @staticmethod
    def install(package):
        """ Install a package using pip """
        proxy = ShellProxy()
        proxy.run([sys.executable, "-m", "pip", "install", package])

    @staticmethod
    def uninstall(package):
        """ Uninstall a package using pip """
        proxy = ShellProxy()
        proxy.run([sys.executable, "-m", "pip", "uninstall", "-y", package])

    @staticmethod
    def load_module_from_file(file_path, module_name=None):
        if module_name is None:
            # use the name of the file a module_name
            path = pathlib.Path(file_path)
            module_name = StringHelper.slugify(path.stem, snakefy=True, to_lower=True)
        spec = importlib.util.spec_from_file_location(module_name, location=file_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    @staticmethod
    def load_module(module_name, package=None):
        if module_name in sys.modules:
            Logger.warning(f"The module '{module_name}' is already loaded")
            return sys.modules[module_name]

        spec = importlib.util.find_spec(module_name, package=package)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.modules[module_name] = module

        return module
