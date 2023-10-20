# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import TypedDict

import botocore.auth
import botocore.credentials
from botocore.awsrequest import AWSRequest
from fastapi.requests import Request

from gws_core.core.exception.exceptions.forbidden_exception import \
    ForbiddenException
from gws_core.core.utils.logger import Logger
from gws_core.credentials.credentials_service import CredentialsService
from gws_core.credentials.credentials_type import CredentialsDataS3


class S3AuthHeader(TypedDict):
    access_key_id: str
    request_date: str
    region_name: str
    service_name: str
    signature: str


class S3ServerAuth:
    """Class to manage auth for s3 server requests
    """

    @classmethod
    def check_s3_server_auth(cls, request: Request) -> None:
        """Check if the request is authorized to access the s3 server
        base on AWS Signature Version 4
        """

        authorization_header = request.headers.get('Authorization')

        if not authorization_header:
            raise ForbiddenException("Authorization header is missing")

        s3_header: S3AuthHeader
        try:
            s3_header = cls._parse_authorization_header(authorization_header)
        except Exception as err:
            Logger.error(f"Error while parsing header: {err}")
            raise ForbiddenException("Authorization header is invalid")

        if not s3_header.get('access_key_id'):
            raise ForbiddenException("Access key id is missing")

        s3_credentials: CredentialsDataS3 = CredentialsService.get_s3_credentials_data_by_access_key(
            s3_header['access_key_id'])

        if not s3_credentials:
            raise ForbiddenException("Access denied")

        expected_signature: str
        try:
            expected_signature = cls._build_signature(request, s3_header, s3_credentials['secret_access_key'])
        except Exception as err:
            Logger.error(f"Error while building signature: {err}")
            raise ForbiddenException("Signature is invalid")

        # check the signature (it checks the secret key)
        if expected_signature != s3_header['signature']:
            raise ForbiddenException("Access denied")

    @classmethod
    def _parse_authorization_header(cls, authorization_header: str) -> S3AuthHeader:
        # Parse the Authorization header to obtain AWS access key, request date, region, service, and signature
        parts = authorization_header.split(", ")
        access_key = parts[0].split("Credential=")[1].split("/")[0]
        request_date = parts[0].split("Credential=")[1].split("/")[1].split("/")[0]
        region = parts[0].split("Credential=")[1].split("/")[2]
        service = parts[0].split("Credential=")[1].split("/")[3]
        signature = parts[2].split("Signature=")[1]
        return {
            'access_key_id': access_key,
            'request_date': request_date,
            'region_name': region,
            'service_name': service,
            'signature': signature
        }

    @classmethod
    def _build_signature(cls, request: Request, header: S3AuthHeader, secret_key: str) -> str:
        """Build the signature for the request to check if it is valid
        """
        # Create a botocore.auth.HmacV1 instance
        # Create SigV4Auth instance
        credentials = botocore.credentials.Credentials(header['access_key_id'], secret_key)
        auth = botocore.auth.SigV4Auth(credentials, header['service_name'], header['region_name'])

        # build the simulated header with the required fields for the signature
        simulated_headers = {'x-amz-date': request.headers.get('x-amz-date'),
                             'x-amz-content-sha256': request.headers.get('x-amz-content-sha256'),
                             'host': request.headers.get('host')}
        if request.headers.get('content-md5'):
            simulated_headers['content-md5'] = request.headers.get('content-md5')

        # simulate a request to generate the signature
        simulated_request = AWSRequest(method=request.method, url=str(request.url), headers=simulated_headers, data=b'')
        simulated_request.context["payload_signing_enabled"] = True  # payload signing is not supported
        simulated_request.context["timestamp"] = request.headers.get('x-amz-date')

        # Generate the canonical request
        canonical_request = auth.canonical_request(simulated_request)

        # # Generate the string to sign
        string_to_sign = auth.string_to_sign(simulated_request, canonical_request)

        # Calculate the expected signature
        return auth.signature(string_to_sign, simulated_request)
