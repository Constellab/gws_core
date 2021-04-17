# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio
import click
from gws.settings import Settings
from gws.logger import Error
from gws.controller import Controller
from gws.model import Experiment, User

@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.pass_context
@click.option('--experiment-uri', help='Experiment uri')
@click.option('--user-uri', help='User uri')
def run_experiment(ctx, experiment_uri, user_uri):
    try:
        user = User.get(User.uri == user_uri)
    except:
        raise Error("gws.cli", "run_experiment", f"A user is requires. IS TEST {Settings.retrieve().is_test}")
        
    if not user.is_authenticated:
        raise Error("gws.cli", "run_experiment", f"The user must be HTTP authenticated")
    
    try:
        e = Experiment.get(Experiment.uri == experiment_uri)
    except Exception as err:
        raise Error("gws.cli", "run_experiment", f"No experiment found with uri {experiment_uri}. Error: {err}")

    if e.is_running:
        raise Error("gws.cli", "run_experiment", f"The experiment is already running")
    elif e.is_finished:
        raise Error("gws.cli", "run_experiment", f"The experiment is already finished")
    else:
        try:
            asyncio.run( e.run(user=user) )
        except Exception as err:
            raise Error("gws.cli", "run_experiment", f"An error occured. Error: {err}")
