# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.utils.settings import Settings


class TaskFileDownloader(FileDownloader):
    """Download external files that are required by a task.
    To init this class, you need to provide the brick name of the task and the message dispatcher of the task.
    For example: TaskFileDownloader(brick_name=MyTaskClass.get_brick_name(), message_dispatcher=self.message_dispatcher)

    It is recommended to use MyTaskClass.get_brick_name() because this defines the destination of the downloader file.
    So the destination will be the same even is your task is overriden by another task.

    :param FileDownloader: _description_
    :type FileDownloader: _type_
    """

    brick_name: str

    def __init__(self, brick_name: str, message_dispatcher: MessageDispatcher = None) -> None:
        """_summary_

        :param brick_name: brick name of the task, use : MyTaskClass.get_brick_name()
        :type brick_name: str
        :param message_dispatcher: object to log the progress message of the downloading in the task.
                                    use : self.message_dispatcher, defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        """
        self.brick_name = brick_name
        settings = Settings.get_instance()
        destination_folder = settings.get_brick_data_dir(brick_name)

        super().__init__(destination_folder, message_dispatcher)
