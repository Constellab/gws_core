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
    
    input_dir="/data/backup/gws/mariadb"
    output_dir="/data/backup/gws/mariadb"

    input_file=""
    output_file=""

    host=""
    port=3306
    process=None
    
    DUMP_FILENAME = "backup.sql.gz"
    CNF_FILENAME = ".local.cnf"
    IN_PROGRESS_FILENAME = ".in_progress"
    LOG_OUR_FILE_NAME = "out.log"
    LOG_ERR_FILE_NAME = "error.log"

    # -- B --

    def build_command(self) -> List[str]:
        raise Error("Not implemented")
    
    # -- I --

    def is_ready(self) -> bool:
        file_path = os.path.join(self.output_dir,self.IN_PROGRESS_FILENAME)
        return not os.path.exists(file_path)

    # -- R --

    def run(self, force: bool=False, wait: bool=False) -> bool:
        if not self.is_ready() and not force:
            Warning("An db process is already in progress")
            return False

        in_progress_file = os.path.join(self.output_dir, self.IN_PROGRESS_FILENAME)
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

    # -- S --

    def set_default_config(self, db_name):
        self.user=db_name
        self.password="gencovery"
        self.db_name=db_name
        self.table_prefix=f"{db_name}_"
        self.output_dir=f"/data/{db_name}/backup/mariadb"
        self.host=f"{db_name}_prod_db"
        self.port=3306

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
        self.db_name = slugify(self.db_name, snakefy=True)                          #slugify string for security
        self.table_prefix = slugify(self.table_prefix, snakefy=True)                #slugify string for security
        self.host = settings.get_maria_db_host(self.db_name)

        if not self.output_file:
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
        self.db_name = slugify(self.db_name, snakefy=True)                          #slugify string for security
        self.table_prefix = slugify(self.table_prefix, snakefy=True)                #slugify string for security
        self.host = settings.get_maria_db_host(self.db_name)

        if not self.input_file:
            self.input_file = os.path.join(self.input_dir, self.DUMP_FILENAME)

        login = f"--defaults-extra-file={self.CNF_FILENAME} --host {self.host} --port {self.port}"
        cmd = [
            f'echo "[client]\nuser={self.user}\npassword={self.password}" > {self.CNF_FILENAME}',
            f'gzip -c -d {self.input_file} | mysql {login} {self.db_name}',
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