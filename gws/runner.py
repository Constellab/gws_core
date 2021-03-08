# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os
import unittest
import click
import importlib
import subprocess
import shutil
import re
from gws.settings import Settings
from gws.logger import Logger, Error

def _run(   ctx=None, uri=False, token=False, test=False, use_prod_biota_db=False, \
            cli=False, runserver=False, ip="0.0.0.0", port="3000", docgen=False, \
            force=False, demo=False):
    
    Logger(is_new_session=True, is_test=test)
    settings = Settings.retrieve()

    if token:
        settings.set_data("token", token)
    
    if uri:
        settings.set_data("uri", uri)
    
    settings.set_data("is_demo", demo)
    
    if not settings.save():
        raise Error("manage", "Cannot save the settings in the database")
    
    #from gws.controller import Controller
    #Controller.register_all_processes()
        
    if runserver:
        settings.set_data("app_host", ip)
        settings.set_data("app_port", port)
        
        if not settings.save():
            raise Error("manage", "Cannot save the settings in the database")
        
        from gws.controller import Controller
        Controller.register_all_processes()
        
        # start app
        from gws.app import App
        app = App()
        app.init()
        app.start()

    elif test:
        if test == "*":
            test = "test*"
        if test == "all":
            test = "test*"
        
        settings.activate_fts(True)
        #settings.data["db_name"] = "test_db.sqlite3"
        settings.data["is_test"] = True        
        settings.data["use_prod_biota_db"] = use_prod_biota_db
        
        if not settings.save():
            raise Error("manage", "Cannot save the settings in the database")
        
        loader = unittest.TestLoader()
        test_suite = loader.discover(".", pattern=test+".py")
        test_runner = unittest.TextTestRunner()
        test_runner.run(test_suite)

    elif cli:
        tab = cli.split(".")
        n = len(tab)
        module_name = ".".join(tab[0:n-1])
        function_name = tab[n-1]
        module = importlib.import_module(module_name)
        t = getattr(module, function_name, None)
        if t is None:
            raise Error("manage", f"CLI not found. Please check that method {cli} is defined")
        else:
            t()

    elif docgen:
        brick_dir = settings.get_cwd()
        from ._sphynx.docgen import docgen
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
@click.option('--uri', help='Lab URI', show_default=True)
@click.option('--token', help='Lab token', show_default=True)
@click.option('--test', help='The name test file to launch (regular expression). Enter "all" to launch all')
@click.option('--use-prod-biota-db', is_flag=True, help='Use the biota production db')
@click.option('--cli', help='Command to run using the command line interface')
@click.option('--runserver', is_flag=True, help='Starts the server')
@click.option('--ip', default="0.0.0.0", help='Server ip', show_default=True)
@click.option('--port', default="3000", help='Server port', show_default=True)
@click.option('--docgen', is_flag=True, help='Generates documentation')
@click.option('--force', is_flag=True, help='Forces documentation generation by removing any existing documentation (used if --docgen is given)')
@click.option('--demo', is_flag=True, help='Run in demo mode [to only use for demonstration tests]')
def run(ctx, uri, token, test, use_prod_biota_db, cli, runserver, ip, port, docgen, force, demo):       
    _run(ctx, uri, token, test, use_prod_biota_db, cli, runserver, ip, port, docgen, force, demo)

