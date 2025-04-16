

from gws_core.core.utils.logger import Logger
from gws_core.impl.s3.s3_server_exception import S3ServerException
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


class S3ServerContext:
    """ Context to support with statement to catch exceptions and convert
    them to S3ServerException.
    It also sets the current user to sys user because in S3 server we don't have a user

    """

    bucket_name: str
    key: str

    def __init__(self, bucket_name: str = None, key: str = None) -> None:
        self.bucket_name = bucket_name
        self.key = key

    def __enter__(self):
        # Authenticate sys user because in S3 server we don't have a user
        CurrentUserService.set_current_user(User.get_and_check_sysuser())
        # Code to set up and acquire resources
        return self  # You can return an object that you want to use in the with block

    def __exit__(self, exc_type, exc_value, traceback):
        # remove the current user
        CurrentUserService.set_current_user(None)
        if exc_value:
            Logger.log_exception_stack_trace(exc_value)
            raise S3ServerException.from_exception(exc_value, self.bucket_name, self.key)
        return True  # You can return True to suppress any further exception
