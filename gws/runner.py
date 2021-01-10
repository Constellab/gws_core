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

def _run(   ctx=None, uri=False, token=False, test=False, db=False, biota_prod_db=False, \
            cli=False, runserver=False, ip="0.0.0.0", port="3000", docgen=False, \
            force=False, show=False, jlab=False, demo=False):
    
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

        settings.data["db_name"] = "test_db.sqlite3"
        settings.data["is_test"] = True        
        settings.data["biota_prod_db"] = biota_prod_db
        
        if db:
            settings.data["db_name"] = db

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
        settings.data["db_name"] = ':memory:'

        if not settings.save():
            raise Error("manage", "Cannot save the settings in the database")
        
        brick_dir = settings.get_cwd()
        doc_folder = "./docs/"
        gen_folder = "./docs/html/"
        rst_folder = "./rst/"

        try:
            if force:
                try:
                    shutil.rmtree(os.path.join(brick_dir, doc_folder), ignore_errors=True)
                except:
                    pass
            
            if not os.path.exists(os.path.join(brick_dir, gen_folder)):             
                os.makedirs(os.path.join(brick_dir, gen_folder))

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
                ], cwd=os.path.join(brick_dir, gen_folder))

            with open(os.path.join(brick_dir, gen_folder, "./source/conf.py"), "r+") as f:
                content = f.read()
                f.seek(0, 0)
                f.write('\n')
                f.write("import os\n")
                f.write("import sys\n")

                dep_dirs = settings.get_dependency_dirs()
                for k in dep_dirs:
                    f.write(f"sys.path.insert(0, '{dep_dirs[k]}')\n")

                f.write("from gws._sphynx import conf\n\n\n")
                f.write(content + '\n')
                f.write("extensions = extensions + conf.extensions\n")
                f.write("exclude_patterns = exclude_patterns + conf.exclude_patterns\n")
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
                ], cwd=os.path.join(brick_dir, gen_folder))

            for f in ['intro.rst', 'usage.rst', 'contrib.rst', 'changes.rst']:
                if os.path.exists(os.path.join(brick_dir, rst_folder, f)):
                    shutil.copyfile(
                        os.path.join(brick_dir, rst_folder, f), 
                        os.path.join(brick_dir,gen_folder,"./source/"+f))

            # insert modules in index
            with open(os.path.join(brick_dir, gen_folder, "./source/index.rst"), "r") as f:
                content = f.read()
                content = content.replace(
                    ":caption: Contents:",
                    ":caption: API documentation:\n\n   modules\n\n")

                content = content.replace(
                    ".. toctree::",

                    (settings.description or "") + "\n\n" +
                    ".. toctree::\n"+
                    "   :hidden:\n\n"+
                    "   self\n\n"+
                    ".. toctree::\n\n"+
                    "   intro\n"+
                    "   usage\n"+
                    "   contrib\n"+
                    "   changes\n\n\n"+
                    ".. toctree::")

            with open(os.path.join(brick_dir, gen_folder, "./source/index.rst"), "w") as f:
                f.write(content)

            subprocess.check_call([
                "sphinx-build",
                "-b",
                "html",
                "./source",
                "./build",
                ], cwd=os.path.join(brick_dir, gen_folder))

            if show:
                import webbrowser
                location = settings.get_dependency_dir(show)
                url = os.path.join(location, gen_folder, "./build/index.html")
                print(url)
                webbrowser.open(f"file://{url}", new=2)
                
        except Exception as err:
            raise Error(f"An error occurred. Error message: {err}")
    elif jlab:
        if jlab == ".":
            lab_dir = settings.get_dependency_dir(settings.name)
        else:
            lab_dir = settings.get_dependency_dir(jlab)

        subprocess.check_call([
            "jupyter", 
            "lab"
            ], cwd=os.path.join(lab_dir))
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
@click.option('--db', help="The name of the database to use")
@click.option('--biota-prod-db', is_flag=True, help='Use to production biota do')
@click.option('--cli', help='Command to run using the command line interface')
@click.option('--runserver', is_flag=True, help='Starts the server')
@click.option('--ip', default="0.0.0.0", help='Server ip', show_default=True)
@click.option('--port', default="3000", help='Server port', show_default=True)
@click.option('--docgen', is_flag=True, help='Generates documentation')
@click.option('--force', is_flag=True, help='Forces documentation generation by removing any existing documentation (used if --docgen is given)')
@click.option('--show', help='Forces documentation generation by removing any existing documentation (used if --docgen is given)')
@click.option('--jlab', help='Runs Jupiter lab', show_default=True)
@click.option('--demo', is_flag=True, help='Run in demo mode [to only use for demonstration tests]')
def run(ctx, uri, token, test, db, biota_prod_db, cli, runserver, ip, port, docgen, force, show, jlab, demo):       
    _run(ctx, uri, token, test, db, biota_prod_db, cli, runserver, ip, port, docgen, force, show, jlab, demo)

