
import botocore.auth
import botocore.credentials
from botocore.awsrequest import AWSRequest
from fastapi.requests import Request

from gws_core.core.exception.exceptions.forbidden_exception import ForbiddenException
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import Logger
from gws_core.credentials.credentials_service import CredentialsService
from gws_core.credentials.credentials_type import CredentialsDataS3, CredentialsDataS3LabServer
from gws_core.impl.s3.abstract_s3_service import AbstractS3Service
from gws_core.impl.s3.datahub_s3_server_service import DataHubS3ServerService
from gws_core.impl.s3.local_s3_server_service import LocalS3ServerService


class S3AuthHeader(BaseModelDTO):
    access_key_id: str | None
    request_date: str
    region_name: str
    service_name: str
    sign_headers: list[str]  # list of the header keys that are included in the signature
    signature: str


class S3ServerAuth:
    """Class to manage auth for s3 server requests"""

    @classmethod
    def check_s3_server_auth(cls, request: Request, bucket: str) -> AbstractS3Service:
        """Check if the request is authorized to access the s3 server
        base on AWS Signature Version 4
        """

        authorization_header = request.headers.get("Authorization")

        if not authorization_header:
            raise ForbiddenException("Authorization header is missing")

        s3_header: S3AuthHeader
        try:
            s3_header = cls._parse_authorization_header(authorization_header)
        except Exception as err:
            Logger.error(f"Error while parsing header: {err}")
            raise ForbiddenException("Authorization header is invalid")

        if not s3_header.access_key_id:
            raise ForbiddenException("Access key id is missing")

        s3_credentials = CredentialsService.get_s3_credentials_data_by_access_key(
            s3_header.access_key_id
        )

        if not s3_credentials:
            raise ForbiddenException("Access denied")

        expected_signature: str
        try:
            expected_signature = cls._build_signature(
                request, s3_header, s3_credentials.secret_access_key
            )
        except Exception as err:
            Logger.error(f"Error while building signature: {err}")
            raise ForbiddenException("Signature is invalid")

        # check the signature (it checks the secret key)
        if expected_signature != s3_header.signature:
            raise ForbiddenException("Access denied")

        if s3_credentials.bucket != bucket:
            raise ForbiddenException("Access denied")

        if isinstance(s3_credentials, CredentialsDataS3LabServer):
            return LocalS3ServerService(s3_credentials.bucket, s3_credentials.bucket_local_path)
        elif isinstance(s3_credentials, CredentialsDataS3):
            return DataHubS3ServerService(s3_credentials.bucket)
        else:
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

        # get the list of the headers that are included in the signature
        sign_headers = parts[1].split("SignedHeaders=")[1].split(";")
        return S3AuthHeader(
            access_key_id=access_key,
            request_date=request_date,
            region_name=region,
            service_name=service,
            signature=signature,
            sign_headers=sign_headers,
        )

    @classmethod
    def _build_signature(cls, request: Request, header: S3AuthHeader, secret_key: str) -> str:
        """Build the signature for the request to check if it is valid"""
        # Create a botocore.auth.HmacV1 instance
        # Create SigV4Auth instance
        credentials = botocore.credentials.Credentials(header.access_key_id, secret_key)
        auth = botocore.auth.SigV4Auth(credentials, header.service_name, header.region_name)

        # Create a simulated request with the headers that are included in the signature
        simulated_headers = {}
        for header_key in header.sign_headers:
            if header_key in request.headers:
                simulated_headers[header_key] = request.headers.get(header_key)

        # simulate a request to generate the signature
        simulated_request = AWSRequest(
            method=request.method, url=str(request.url), headers=simulated_headers, data=b""
        )
        simulated_request.context["payload_signing_enabled"] = (
            True  # payload signing is not supported
        )
        simulated_request.context["timestamp"] = request.headers.get("x-amz-date")

        # Generate the canonical request
        canonical_request = auth.canonical_request(simulated_request)

        # # Generate the string to sign
        string_to_sign = auth.string_to_sign(simulated_request, canonical_request)

        # Calculate the expected signature
        return auth.signature(string_to_sign, simulated_request)
