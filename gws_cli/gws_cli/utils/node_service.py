import subprocess
from pathlib import Path

import typer


class NodeService:
    """Service for managing Node.js installation and related operations"""

    @staticmethod
    def is_node_installed() -> bool:
        """Check if Node.js and npm are installed

        Returns:
            bool: True if both node and npm are available, False otherwise
        """
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
            subprocess.run(["npm", "--version"], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def install_node() -> int:
        """Install Node.js using NVM (Node Version Manager)

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        script_dir = Path(__file__).parent.parent / "scripts"
        script_path = script_dir / "install-node.sh"

        if not script_path.exists():
            typer.echo(f"Error: Install script not found at {script_path}", err=True)
            return 1

        typer.echo("Starting Node.js installation...")

        try:
            # Execute the bash script
            result = subprocess.run(["bash", str(script_path)], check=True, capture_output=False)

            if result.returncode == 0:
                typer.echo("Node.js installation completed successfully!")
                return 0
            else:
                typer.echo("Node.js installation failed!")
                return 1

        except subprocess.CalledProcessError as e:
            typer.echo(f"Error during Node.js installation: {e}", err=True)
            return 1
        except Exception as e:
            typer.echo(f"Unexpected error: {e}", err=True)
            return 1
