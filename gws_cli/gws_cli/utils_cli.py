import typer

from gws_cli.utils.node_service import NodeService
from gws_cli.utils.screenshot_service import ScreenshotService

app = typer.Typer(help="Utility commands for development environment setup")


@app.command("install-node", help="Install Node.js via NVM")
def install_node():
    """Install Node.js using NVM (Node Version Manager)"""
    exit_code = NodeService.install_node()
    if exit_code != 0:
        raise typer.Exit(exit_code)


@app.command("screenshot", help="Take a screenshot of a web application")
def screenshot(
    url: str = typer.Option(
        "http://localhost:8511", "--url", "-u", help="Base URL of the application"
    ),
    route: str = typer.Option("/", "--route", "-r", help="Route to navigate to"),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for the screenshot (default: /lab/user/app_screenshot.png)",
    ),
    no_logs: bool = typer.Option(False, "--no-logs", help="Don't save console logs"),
    headless: bool = typer.Option(
        True, "--headless/--no-headless", help="Run browser in headless mode (default: headless)"
    ),
):
    """
    Take a screenshot of a web application using Playwright.
    Automatically installs Playwright if not already installed.

    Example:
        gws utils screenshot --route /dashboard --output ./screenshots/dashboard.png
    """
    exit_code = ScreenshotService.take_screenshot(
        url=url, route=route, output_path=output, save_console_logs=not no_logs, headless=headless
    )
    if exit_code != 0:
        raise typer.Exit(exit_code)
