# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio

import click

from gws.exception.bad_request_exception import BadRequestException

from .experiment import Experiment
from .settings import Settings
from .user import User


@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.pass_context
@click.option('--experiment-uri', help='Experiment uri')
@click.option('--user-uri', help='User uri')
def run_experiment(ctx, experiment_uri, user_uri):
    settings = Settings.retrieve()

    try:
        user = User.get(User.uri == user_uri)
    except Exception as err:
        raise BadRequestException(
            f"No user found with uri '{user_uri}'. Flags: is_prod={settings.is_prod}, is_test={settings.is_test}. Error: {err}") from err

    if not user.is_authenticated:
        raise BadRequestException(f"The user must be HTTP authenticated")

    try:
        e = Experiment.get(Experiment.uri == experiment_uri)
    except Exception as err:
        raise BadRequestException(
            f"No experiment found with uri {experiment_uri}. Error: {err}") from err

    if e.is_running:
        raise BadRequestException(f"The experiment is already running")
    elif e.is_finished:
        raise BadRequestException(f"The experiment is already finished")
    else:
        try:
            asyncio.run(e.run(user=user, wait_response=True))
        except Exception as err:
            raise BadRequestException(
                f"An error occured. Error: {err}") from err
