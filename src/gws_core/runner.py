# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import importlib
import os
import unittest
from copy import Error
from unittest.suite import BaseTestSuite

import click

from .app import App
from .core.exception.exceptions import BadRequestException
from .core.utils.logger import Logger
from .core.utils.settings import Settings


def _run(ctx, uri="", token="", test="",
         cli=False, cli_test=False, runserver=False, runmode="dev",
         ip="0.0.0.0", port="3000", docgen=False,
         force=False, log_level: str = None):

    is_test = bool(test or cli_test)
    is_prod = (runmode == "prod")
    Logger(level=log_level, _is_experiment_process=cli)

    settings = Settings.retrieve()
    settings.set_data("app_host", ip)
    settings.set_data("app_port", port)
    settings.set_data("token", token)
    settings.set_data("uri", uri)
    settings.set_data("is_prod", is_prod)
    settings.set_data("is_debug", True)
    settings.set_data("is_test", is_test)

    if is_prod:
        # Deactivate any test in production mode
        settings.set_data("test", "")
        settings.set_data("is_test", False)

    if not settings.save():
        raise BadRequestException("Cannot save the settings in the database")

    if runserver:
        # start app
        App.start(ip=ip, port=port)
    elif cli:
        tab = cli.split(".")
        n = len(tab)
        module_name = ".".join(tab[0:n-1])
        function_name = tab[n-1]
        module = importlib.import_module(module_name)
        func = getattr(module, function_name, None)
        if func is None:
            raise BadRequestException(
                f"Please check that method {cli} is defined")
        else:
            func()
    elif test:
        if test in ["*", "all"]:
            test = "test*"

        tests: str = test.split(' ')
        loader = unittest.TestLoader()
        __cdir__ = os.path.dirname(os.path.abspath(__file__))

        test_suite: BaseTestSuite = BaseTestSuite()

        for test_file in tests:
            test_suite.addTests(loader.discover(os.path.join(
                __cdir__, "../../tests/"), pattern=test_file+".py"))
        # test_suite = loader.discover(os.path.join(
            # __cdir__, "../../tests/"), pattern=test+".py")

        test_runner = unittest.TextTestRunner()

        if test_suite.countTestCases() == 0:
            raise Error(f"No test file with name {test} found")

        test_runner.run(test_suite)
    elif docgen:

        brick_dir = settings.get_cwd()
        docgen(settings.name, brick_dir, settings, force=force)
    else:
        # only load gws environmenet
        pass

    print(f"Log file: {Logger.get_file_path()}")


@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.pass_context
@click.option('--uri', default="", help='Lab URI', show_default=True)
@click.option('--token', default="", help='Lab token', show_default=True)
@click.option('--test', default="", help='The name test file to launch (regular expression). Enter "all" to launch all the tests')
@click.option('--cli', default="", help='Command to run using the command line interface')
@click.option('--cli_test', is_flag=True, help='Use command line interface in test mode')
@click.option('--runserver', is_flag=True, help='Starts the server')
@click.option('--runmode', default="dev", help='Starting mode (dev or prod). Defaults to dev')
@click.option('--ip', default="0.0.0.0", help='Server IP', show_default=True)
@click.option('--port', default="3000", help='Server port', show_default=True)
@click.option('--docgen', is_flag=True, help='Generates documentation')
@click.option('--force', is_flag=True, help='Forces documentation generation by removing any existing documentation (used if --docgen is given)')
@click.option('--log_level', default="INFO", help='Level for the logs', show_default=True)
def run(ctx, uri, token, test, cli, cli_test, runserver, runmode, ip, port, docgen, force, log_level):
    _run(
        ctx,
        uri=uri,
        token=token,
        test=test,
        cli=cli,
        cli_test=cli_test,
        runserver=runserver,
        runmode=runmode,
        ip=ip,
        port=port,
        docgen=docgen,
        force=force,
        log_level=log_level
    )
