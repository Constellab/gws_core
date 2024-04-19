

from fastapi import HTTPException, status

from gws_core.core.utils.xml_helper import XMLHelper


class S3ServerException(HTTPException):
    code: str
    message: str
    key: str
    bucket_name: str

    def __init__(self, status_code: int, code: str, message: str,
                 bucket_name: str, key: str = None) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.key = key
        self.bucket_name = bucket_name

    @staticmethod
    def from_http_exception(exc: HTTPException, bucket_name: str = None, key: str = None) -> 'S3ServerException':
        return S3ServerException(status_code=exc.status_code, code='http_error', message=exc.detail,
                                 bucket_name=bucket_name, key=key)

    @staticmethod
    def from_exception(exc: Exception, bucket_name: str = None, key: str = None) -> 'S3ServerException':
        if isinstance(exc, S3ServerException):
            return exc
        elif isinstance(exc, HTTPException):
            return S3ServerException.from_http_exception(exc, bucket_name, key)
        else:
            return S3ServerException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, code='internal_error',
                                     message=str(exc), bucket_name=bucket_name, key=key)

    def to_xml(self) -> str:
        json_ = {
            'Error': {
                'Code': self.code,
                'Message': self.message,
                'BucketName': self.bucket_name
            }
        }

        if self.key:
            json_['Error']['Key'] = self.key
            json_['Error']['Resource'] = f'/{self.bucket_name}/{self.key}'
        else:
            json_['Error']['Resource'] = f'/{self.bucket_name}'

        return XMLHelper.dict_to_xml(json_)


class S3ServerNoSuchBucket(S3ServerException):
    """Exception to raise when a bucket doesn't exist
    """

    def __init__(self, bucket_name: str) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND,
                         code='NoSuchBucket',
                         message='The specified bucket does not exist.',
                         bucket_name=bucket_name)


class S3ServerNoSuchKey(S3ServerException):
    """Exception to raise when a key doesn't exist in a bucket
    """

    def __init__(self, bucket_name: str, key: str) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND,
                         code='NoSuchKey',
                         message='The specified key does not exist.',
                         bucket_name=bucket_name, key=key)
