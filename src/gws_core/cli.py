# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import asyncio

import click

from .core.exception.exception_handler import ExceptionHandler
from .core.exception.exceptions import BadRequestException
from .experiment.experiment_service import ExperimentService


@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.pass_context
@click.option('--experiment-uri', help='Experiment uri')
@click.option('--user-uri', help='User uri')
def run_experiment(ctx, experiment_uri, user_uri):
    try:
        asyncio.run(ExperimentService.run_experiment_in_cli(
            experiment_uri, user_uri))
    except Exception as err:
        ExceptionHandler.handle_exception(None, err)
        raise BadRequestException(
            f"An error occured. Error: {err}") from err
