

import os
import subprocess
from typing import List

from gws_core.core.db.db_config import DbConfig
from gws_core.core.utils.logger import Logger

from ..exception.exceptions import BadRequestException


class MySQLBase:
    """
    MySQLBase class
    """

    db_config: DbConfig
    input_dir = "/data/gws/backup/mariadb"
    output_dir = "/data/gws/backup/mariadb"

    input_file = ""
    output_file = ""

    process = None

    DUMP_FILENAME = "backup.sql.gz"
    CNF_FILENAME = ".local.cnf"
    IN_PROGRESS_FILENAME = ".in_progress"
    LOG_OUR_FILE_NAME = "out.log"
    LOG_ERR_FILE_NAME = "error.log"

    def __init__(self, db_config: DbConfig, output_dir: str) -> None:
        self.db_config = db_config
        self.output_dir = f"/data/{output_dir}/backup/mariadb"

    # -- B --

    def build_command(self) -> List[str]:
        raise BadRequestException("Not implemented")

    # -- I --

    def is_ready(self) -> bool:
        file_path = os.path.join(self.output_dir, self.IN_PROGRESS_FILENAME)
        return not os.path.exists(file_path)

    # -- R --

    def run(self, force: bool = False, wait: bool = False) -> bool:
        if not self.is_ready() and not force:
            Logger.error("An db process is already in progress")
            return False

        in_progress_file = os.path.join(
            self.output_dir, self.IN_PROGRESS_FILENAME)
        log_out_file = os.path.join(self.output_dir, self.LOG_OUR_FILE_NAME)
        log_err_file = os.path.join(self.output_dir, self.LOG_ERR_FILE_NAME)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        if os.path.exists(log_out_file):
            os.remove(log_out_file)

        if os.path.exists(log_err_file):
            os.remove(log_err_file)

        cmd = self.build_command()
        cmd = [
            f'touch {in_progress_file}',
            *cmd,
            f'rm -f {in_progress_file}'
        ]

        proc = subprocess.Popen(
            " && ".join(cmd),
            shell=True,
            cwd=self.output_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        if wait:
            try:
                proc.communicate()
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()

        return True

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

    def build_command(self) -> List[str]:
        if not self.output_file:
            self.output_file = os.path.join(
                self.output_dir, self.DUMP_FILENAME)

        login = f'--defaults-extra-file={self.CNF_FILENAME} --host {self.db_config["host"]} --port {self.db_config["port"]}'
        cmd = [
            f'echo "[client]\nuser={self.db_config["user"]}\npassword={self.db_config["password"]}" > {self.CNF_FILENAME}',
            f'mysql {login} -N information_schema -e "select table_name from tables where table_schema = \'{self.db_config["db_name"]}\'" | xargs -I"{{}}" mysqldump {login} {self.db_config["db_name"]} {{}} | gzip -f --best --rsyncable > {self.output_file}',
            f'rm -f {self.CNF_FILENAME}',
        ]
        return cmd


# ####################################################################
#
# MySQLLoad
#
# ####################################################################

class MySQLLoad(MySQLBase):
    """
    MySQLImport process

    This class load tables of mysql databases
    """

    def build_command(self) -> List[str]:
        if not self.input_file:
            self.input_file = os.path.join(self.input_dir, self.DUMP_FILENAME)

        login = f'--defaults-extra-file={self.CNF_FILENAME} --host {self.db_config["host"]} --port {self.db_config["port"]}'
        cmd = [
            f'echo "[client]\nuser={self.db_config["user"]}\npassword={self.db_config["password"]}" > {self.CNF_FILENAME}',
            f'gzip -c -d {self.input_file} | mysql {login} {self.db_config["db_name"]}',
            f'rm -f {self.CNF_FILENAME}'
        ]
        return cmd

# # ####################################################################
# #
# # MySQLDrop
# #
# # ####################################################################

# class MySQLDrop(MySQLBase):
#     """
#     MySQLDrop process

#     This class drops tables of mysql databases
#     """

#     def build_command(self) -> List[str]:
#         settings = Settings.get_instance()
#         self.host = settings.get_maria_db_host()
#         self.db_name = slugify(self.db_name, snakefy=True)                          #slugify string for security
#         self.table_prefix = slugify(self.table_prefix, snakefy=True)                #slugify string for security
#         login = f"--defaults-extra-file={self.CNF_FILENAME} --host {self.host} --port {self.port}"
#         cmd = [
#             f'echo "[client]\nuser={self.user}\npassword={self.password}" > {self.CNF_FILENAME}',
#             f'mysql {login} -NB information_schema -e "select table_name from tables where table_schema = \'{self.db_name}\' and table_name like \'{self.table_prefix}%\'" | xargs -I"{{}}" mysql {login} -D {self.db_name} -e "SET FOREIGN_KEY_CHECKS = 0; DROP TABLE IF EXISTS {{}}; SET FOREIGN_KEY_CHECKS = 1;"',
#             f'rm -f {self.CNF_FILENAME}',
#         ]
#         return cmd
