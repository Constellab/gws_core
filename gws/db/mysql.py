# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import tempfile
import subprocess

from gws.shell import Shell
from gws.file import File
from gws.settings import Settings
from gws.utils import slugify
from gws.system import SysProc

class MySQLBase:
    """
    MySQLBase class
    """

    user="gws"
    password="gencovery"
    db_name="gws"
    table_prefix="gws_"
    output_dir="/data/backup/mysql/"
    output_file=""
    host=""
    port=3306
    process=None

# ####################################################################
#
# MySQLDump
#
# ####################################################################

class MySQLDump(MySQLBase):
    """
    MySQLDump class

    This class dumps mysql databases
    """

    DUMP_FILE =  "backup.sql.gz"
    IN_PROGRESS_FILENAME = ".mysql_dump_in_progress"

    def is_in_progress(self) -> bool:
        file_path = os.path.join(self.output_dir,self.IN_PROGRESS_FILENAME)
        return os.path.exists(file_path)

    def build_command(self) -> list:
        settings = Settings.retrieve()
        self.host = settings.get_maria_db_host()
        self.db_name = slugify(self.db_name, snakefy=True)                          #slugify string for security
        self.table_prefix = slugify(self.table_prefix, snakefy=True)                #slugify string for security
        self.output_file = os.path.join(self.output_dir, self.DUMP_FILE)
        in_progress_file = os.path.join(self.output_dir, self.IN_PROGRESS_FILENAME)
        cnf_file = ".local.cnf"

        login = f"--defaults-extra-file={cnf_file} --host {self.host} --port {self.port}"
        cmd = [
            f'touch {in_progress_file}',
            f'echo "[client]\nuser={self.user}\npassword={self.password}" > {cnf_file}',
            f'mysql {login} -N information_schema -e "select table_name from tables where table_schema = \'{self.db_name}\' and table_name like \'{self.table_prefix}%\'" | xargs -I"{{}}" mysqldump {login} {self.db_name} {{}} | gzip -f --best --rsyncable > {self.output_file}',
            f'rm -f {cnf_file}',
            f'rm -f {in_progress_file}'
        ]

        return cmd

    def run(self, force: bool=False) -> bool:
        if self.is_in_progress() and not force:
            return False

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        cmd = self.build_command()
        self.process = SysProc.popen(
            " && ".join(cmd),
            cwd=self.output_dir,
            shell=True,
            stdout=subprocess.PIPE
        )
        return True

# ####################################################################
#
# MySQLDrop
#
# ####################################################################

class MySQLDrop(MySQLBase):
    """
    MySQLDrop process

    This class drops tables of mysql databases
    """

    def build_command(self) -> list:
        settings = Settings.retrieve()
        self.host = settings.get_maria_db_host()
        self.db_name = slugify(self.db_name, snakefy=True)                          #slugify string for security
        self.table_prefix = slugify(self.table_prefix, snakefy=True)                #slugify string for security
        login = f"--defaults-extra-file=local.cnf --host {self.host} --port {self.port}"
        cmd = [
            f'echo "[client]\nuser={self.user}\npassword={self.password}" > local.cnf',
            f'mysql {login} -NB  information_schema -e "select table_name from tables where table_schema = \'{self.db_name}\' and table_name like \'{self.table_prefix}%\'" | xargs -I"{{}}" mysql {login} {self.db_name} -e "SET FOREIGN_KEY_CHECKS = 0; DROP TABLE {{}}; SET FOREIGN_KEY_CHECKS = 1;"'
        ]
        return cmd