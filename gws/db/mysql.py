# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
from typing import List

from gws.settings import Settings
from gws.utils import slugify
from gws.system import SysProc
from gws.logger import Error

class MySQLBase:
    """
    MySQLBase class
    """

    user="gws"
    password="gencovery"
    db_name="gws"
    table_prefix="gws_"
    output_dir="/data/backup/mariadb/"
    output_file=""
    host=""
    port=3306
    process=None
    
    DUMP_FILENAME = "backup.sql.gz"
    CNF_FILENAME = ".local.cnf"
    IN_PROGRESS_FILENAME = ".in_progress"
    LOG_OUR_FILE_NAME = "out.log"
    LOG_ERR_FILE_NAME = "error.log"

    def is_ready(self) -> bool:
        file_path = os.path.join(self.output_dir,self.IN_PROGRESS_FILENAME)
        return not os.path.exists(file_path)

    def build_command(self) -> List[str]:
        raise Error("Not implemented")

    def run(self, force: bool=False, wait: bool=False) -> bool:
        if not self.is_ready() and not force:
            Warning("An db process is already in progress")
            return False

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        in_progress_file = os.path.join(self.output_dir, self.IN_PROGRESS_FILENAME)
        log_out_file = os.path.join(self.output_dir, self.LOG_OUR_FILE_NAME)
        log_err_file = os.path.join(self.output_dir, self.LOG_ERR_FILE_NAME)

        cmd = self.build_command()
        cmd = [
            f'touch {in_progress_file}',
            *cmd,
            f'rm -f {in_progress_file}'
        ]

        with open(log_out_file, 'w') as f_out:
            with open(log_err_file, 'w') as f_err:
                self.process = SysProc.popen(
                    " && ".join(cmd),
                    cwd=self.output_dir,
                    shell=True,
                    stdout=f_out,
                    stderr=f_err
                )

                if wait:
                    self.process.wait()
        
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
        settings = Settings.retrieve()
        self.host = settings.get_maria_db_host()
        self.db_name = slugify(self.db_name, snakefy=True)                          #slugify string for security
        self.table_prefix = slugify(self.table_prefix, snakefy=True)                #slugify string for security
        self.output_file = os.path.join(self.output_dir, self.DUMP_FILENAME)
        login = f"--defaults-extra-file={self.CNF_FILENAME} --host {self.host} --port {self.port}"
        cmd = [
            f'echo "[client]\nuser={self.user}\npassword={self.password}" > {self.CNF_FILENAME}',
            f'mysql {login} -N information_schema -e "select table_name from tables where table_schema = \'{self.db_name}\' and table_name like \'{self.table_prefix}%\'" | xargs -I"{{}}" mysqldump {login} {self.db_name} {{}} | gzip -f --best --rsyncable > {self.output_file}',
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
        settings = Settings.retrieve()
        self.host = settings.get_maria_db_host()
        self.db_name = slugify(self.db_name, snakefy=True)                          #slugify string for security
        self.table_prefix = slugify(self.table_prefix, snakefy=True)                #slugify string for security
        self.output_file = os.path.join(self.output_dir, self.DUMP_FILENAME)
        login = f"--defaults-extra-file={self.CNF_FILENAME} --host {self.host} --port {self.port}"
        cmd = [
            f'echo "[client]\nuser={self.user}\npassword={self.password}" > {self.CNF_FILENAME}',
            f'gzip -c -d {self.output_file} | mysql {login} {self.db_name}',
            f'rm -f {self.CNF_FILENAME}',
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
#         settings = Settings.retrieve()
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