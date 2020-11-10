# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import click
from gws.settings import Settings
from gws.logger import Logger

@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.pass_context
@click.option('--user', '-u', help='User name')
def hello(ctx,user):
    print("Hello", user)
    print("Welcome in the CLI!")