import typer
from gws_core.manage import AppManager

app = typer.Typer()


@app.command("reset")
def reset_dev_env():
    delete = typer.confirm(
        "Are you sure you want to delete all the data of the dev environment ? The production data will not be affected. This action is irreversible.")

    if not delete:
        typer.echo("The data was not deleted.")
        raise typer.Abort()

    # load_gws_core()
    AppManager.reset_environment()
