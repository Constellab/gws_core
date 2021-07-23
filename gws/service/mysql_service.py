# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from ..db.mysql import MySQLDump, MySQLLoad
from ..http import *
from ..requests import Requests
from .base_service import BaseService


class MySQLService(BaseService):

    @classmethod
    def dump_db(cls, db_name, force: bool=False, wait:bool=False) -> str:
        """
        Dump an MySQL db

        :param db_name: The name of the db
        :type db_name: `str`
        :param force: True to not check if a dump process if already in progress, False otherwise
        :type force: `bool`
        :param wait: True wait for the process to finish, False otherwise. If True, the process is run in background.
        :type wait: `bool`
        :return: The path of the dump file
        :rtype: `str`
        """

        dump = MySQLDump()
        dump.set_default_config(db_name)
        dump.run(force=force, wait=wait)
        return dump.output_file

    # -- L --

    @classmethod
    def load_db(cls, db_name, local_file_path: str=None, remote_file_url: str=None,  force: bool=False, wait:bool=False):
        """
        Load an MySQL db

        :param db_name: The name of the db
        :type db_name: `str`
        :param local_file_path: The path of the local file to download and load
        :type local_file_path: `str`
        :param remote_file_url: The url of the remote file to download and load. The local file is checked in priority.
        :type remote_file_url: `str`
        :param force: True to not check if a process if already in progress, False otherwise
        :type force: `bool`
        :param wait: True wait for the process to finish, False otherwise. If True, the process is run in background.
        :type wait: `bool`
        """

        load = MySQLLoad()
        load.set_default_config(db_name)
        if local_file_path:
            if os.path.exists(local_file_path):
                load.input_file = local_file_path
        elif remote_file_url:
            Requests.download(
                remote_file_url,
                load.input_dir,
                load.DUMP_FILENAME
            )
        else:
            # use default MySQLLoad configs
            pass

        load.run(force=force, wait=wait)

    # -- R --


