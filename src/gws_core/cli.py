# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio

import click

from gws_core.experiment.experiment_service import ExperimentService

from .core.exception import BadRequestException
from .core.exception.exception_handler import ExceptionHandler
from .core.utils.settings import Settings
from .user.user import User


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
        user: User = User.get(User.uri == user_uri)
    except Exception as err:
        raise BadRequestException(
            f"No user found with uri '{user_uri}'. Flags: is_prod={settings.is_prod}, is_test={settings.is_test}. Error: {err}") from err

    if not user.is_authenticated:
        raise BadRequestException("The user must be HTTP authenticated")

    try:
        asyncio.run(ExperimentService.run_experiment(
            experiment_uri=experiment_uri, user=user, wait_response=True))
    except Exception as err:
        ExceptionHandler.handle_exception(err)
        raise BadRequestException(
            f"An error occured. Error: {err}") from err
