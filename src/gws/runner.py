#
# Core GWS manage module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#


import sys
import os
import unittest
import argparse
import uvicorn
import click
import importlib

from gws.settings import Settings

@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.pass_context
@click.option('--test', '-t', help='The name test file to launch (regular expression)')
@click.option('--db', '-d', help="The name of the database to use")
@click.option('--cli', '-c', help='Command to run using the command line interface')
@click.option('--runserver', '-r', is_flag=True, help='Starts the server')

def run(ctx, test, db, cli, runserver):
    settings = Settings.retrieve()

    if runserver:   
        from gws.prism.controller import Controller
        from gws.prism.app import App
        
        Controller.is_query_params = False
        app = App()
        app.start()

    elif test:
        if test == "*":
            test = "test*"
        if test == "all":
            test = "test*"

        settings.data["db_name"] = 'db_test.sqlite3'
        settings.data["is_test"] = True

        if db:
            settings.data["db_name"] = db

        if not settings.save():
            raise Exception("manage", "Cannot save the settings in the database")
        
        loader = unittest.TestLoader()
        test_suite = loader.discover(".", pattern=test+"*.py")
        test_runner = unittest.TextTestRunner()
        test_runner.run(test_suite)

    elif cli:
        tab = cli.split(".")
        n = len(tab)
        module_name = ".".join(tab[0:n-1])
        function_name = tab[n-1]
        module = importlib.import_module(module_name)
        getattr(module, function_name)()