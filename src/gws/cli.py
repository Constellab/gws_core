import click
from gws.settings import Settings

@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.pass_context
@click.option('--name', '-n', help='Your name')
def hello(ctx,name):
    print("Hello", name)
    print("Welcome in the CLI!")