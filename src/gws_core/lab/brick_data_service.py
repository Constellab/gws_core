# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import List, Literal, TypedDict

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper


class BrickData(TypedDict):

    brick_name: str
    fs_node_name: str
    fs_node_size: int
    fs_node_path: str
    fs_node_type: Literal['file', 'folder']


class BrickDataService():

    @classmethod
    def get_brick_data_list(cls) -> List[BrickData]:
        """
        Get the list of brick data for a brick.
        """
        settings = Settings.get_instance()
        data_folder = settings.get_brick_data_main_dir()

        FileHelper.create_dir_if_not_exist(data_folder)

        brick_data_list: List[BrickData] = []

        for brick_name in os.listdir(data_folder):
            brick_data_path = os.path.join(data_folder, brick_name)

            # keep only the folder, it corresponds to a brick
            if not FileHelper.is_dir(brick_data_path):
                continue

            # retrieve all file and folder in the brick
            for node_name in os.listdir(brick_data_path):
                sub_node_path = os.path.join(brick_data_path, node_name)

                brick_data_list.append({
                    'brick_name': brick_name,
                    'fs_node_name': node_name,
                    'fs_node_size': FileHelper.get_size(sub_node_path),
                    'fs_node_path': sub_node_path,
                    'fs_node_type': 'file' if FileHelper.is_file(sub_node_path) else 'folder',
                })

        return brick_data_list

    @classmethod
    def delete_brick_data(cls, fs_node_path: str):
        """
        Delete the brick data for a brick.
        """
        main_dir = Settings.get_instance().get_brick_data_main_dir()
        if not fs_node_path.startswith(main_dir):
            raise BadRequestException(f'Path {fs_node_path} is not a brick data path.')
        FileHelper.delete_node(fs_node_path)

    @classmethod
    def delete_all_brick_data(cls):
        """
        Delete all brick data.
        """
        FileHelper.delete_dir_content(Settings.get_instance().get_brick_data_main_dir())
