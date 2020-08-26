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

def _run(ctx=None, test=False, db=False, cli=False, runserver=False, docgen=False, force=False, pull=False, push=False, tag=""):
    settings = Settings.retrieve()

    from gws.logger import Logger
    Logger(is_new_session=True, is_test=test)
    
    if runserver:   
        from gws.prism.controller import Controller
        Controller.is_query_params = False

        # dynamical inheritance of App
        dep_module_names = settings.get_dependency_names()    
        apps_t = tuple()
        for name in dep_module_names:
            try:
                module = importlib.import_module(name+".app")
                t = getattr(module, "App", None)
                if not t is None:
                    apps_t = apps_t + (t,)
            except Exception as err:
                Logger.error(Exception(f"Cannot run server. It seems that your App module '{name}' is not well implemented.\n Error message: {err}"))
        
        routes = []
        for app_t in apps_t:
            app_t.init_routes()
            routes = routes + app_t.routes

        current_app_t = type("App", apps_t, {})
        current_app_t.routes = routes

        #print(current_app_t.routes)
        
        app = current_app_t()
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
            Logger.error(Exception("manage", "Cannot save the settings in the database"))
        
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
        getattr(module, function_name)()
    
    elif docgen:
        settings.data["db_name"] = ':memory:'

        if not settings.save():
            Logger.error(Exception("manage", "Cannot save the settings in the database"))
        
        app_dir = settings.get_cwd()
        gen_folder = "./docs/html/"

        try:
            if force:
                try:
                    shutil.rmtree(os.path.join(app_dir, gen_folder), ignore_errors=True)
                except:
                    pass

            if not os.path.exists(os.path.join(app_dir, gen_folder)):
                os.mkdir(os.path.join(app_dir, gen_folder))

            subprocess.check_call([
                "sphinx-quickstart", "-q",
                f"-p{settings.title}",
                f"-a{settings.authors}",
                f"-v{settings.version}",
                f"-l en",
                "--sep",
                "--ext-autodoc",
                "--ext-todo",
                "--ext-coverage",
                "--ext-mathjax",
                "--ext-ifconfig",
                "--ext-viewcode",
                "--ext-githubpages",
                ], cwd=os.path.join(app_dir, gen_folder))
            
            with open(os.path.join(app_dir, gen_folder, "./source/conf.py"), "r+") as f:
                content = f.read()
                f.seek(0, 0)
                f.write('\n')
                f.write("import os\n")
                f.write("import sys\n")
                f.write("wd = os.path.abspath('../../../')\n")
                f.write("sys.path.insert(0, os.path.join(wd,'../gws-py'))\n")
                f.write("from gws import sphynx_conf\n\n\n")
                f.write(content + '\n')
                f.write("extensions = extensions + sphynx_conf.extensions\n")
                f.write("exclude_patterns = exclude_patterns + sphynx_conf.exclude_patterns\n")
                f.write("html_theme = 'sphinx_rtd_theme'")

            subprocess.check_call([
                "sphinx-apidoc",
                "-M",
                f"-H{settings.title}",
                f"-A{settings.authors}",
                f"-V{settings.version}",
                "-f",
                "-o", "./source",
                os.path.join("../../",settings.name)
                ], cwd=os.path.join(app_dir, gen_folder))

            for f in ['intro.rst', 'usage.rst', 'contrib.rst', 'changes.rst']:
                if os.path.exists(os.path.join(app_dir,"./docs/"+f)):
                    shutil.copyfile(
                        os.path.join(app_dir,"./docs/"+f), 
                        os.path.join(app_dir,"./docs/html/source/"+f))

            # insert modules in index
            with open(os.path.join(app_dir, gen_folder, "./source/index.rst"), "r") as f:
                content = f.read()
                content = content.replace(
                    ":caption: Contents:",
                    ":caption: API documentation:\n\n   modules\n\n")

                content = content.replace(
                    ".. toctree::",

                    settings.description + "\n\n" +
                    ".. toctree::\n"+
                    "   :hidden:\n\n"+
                    "   self\n\n"+
                    ".. toctree::\n\n"+
                    "   intro\n"+
                    "   usage\n"+
                    "   contrib\n"+
                    "   changes\n\n\n"+
                    ".. toctree::")
                
            with open(os.path.join(app_dir, gen_folder, "./source/index.rst"), "w") as f:
                f.write(content)

            subprocess.check_call([
                "sphinx-build",
                "-b",
                "html",
                "./source",
                "./build",
                ], cwd=os.path.join(app_dir, gen_folder))

        except:
            pass
    
    elif pull:
        app_server = ""
        docs_server = ""
        # pull app

        # pull docs

    elif push:
        app_server = ""
        docs_server = ""
        # push app

        # push docs
        if not os.path.exists(os.path.join(app_dir, gen_folder)):
            # send html doc to a remote server
            pass

    else:
        # only load gws environmenet
        pass

        #settings.data["db_name"] = ':memory:'
        #if not settings.save():
        #    Logger.error(Exception("manage", "Cannot save the settings in the database"))
    
    print(f"Log file: {Logger.get_file_path()}")
        

@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.pass_context
@click.option('--test', '-t', help='The name test file to launch (regular expression)')
@click.option('--db', '-d', help="The name of the database to use")
@click.option('--cli', '-c', help='Command to run using the command line interface')
@click.option('--runserver', is_flag=True, help='Starts the server')
@click.option('--docgen', is_flag=True, help='Generate documentation')
@click.option('--force', "-f", is_flag=True, help='Force documentation generation by removing any existing documentation (used if --docgen is given)')
@click.option('--pull', is_flag=True, help='Update the app')
@click.option('--push', is_flag=True, help='Publish the app')
@click.option('--tag', help='Tag of the published app (default is the current version)')
def run(ctx, test, db, cli, runserver, docgen, force, pull, push, tag):
    _run(ctx, test, db, cli, runserver, docgen, force, pull, push, tag)

