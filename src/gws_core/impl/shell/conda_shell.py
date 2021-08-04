# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from .shell import Shell


class CondaShell(Shell):
    """
    CondaShell process.

    This class is a proxy to run user shell commands through the Python method `subprocess.run`.
    """

    _shell_mode = True

    def _format_command_in_shell_mode(self, user_cmd: list) -> str:
        if isinstance(user_cmd, list):
            user_cmd = [str(c) for c in user_cmd]
            user_cmd = ' '.join(user_cmd)

        cmd = 'bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate base && ' + user_cmd + '"'
        return cmd
