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
@click.option('--experiment-id', help='Experiment id')
@click.option('--user-id', help='User id')
def run_experiment(ctx, experiment_id, user_id):
    try:
        asyncio.run(ExperimentService.run_experiment_in_cli(
            experiment_id, user_id))
    except Exception as err:
        ExceptionHandler.handle_exception(None, err)
        raise BadRequestException(
            f"An error occured. Error: {err}") from err
