# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import Depends
from fastapi.params import Query
from fastapi.requests import Request
from fastapi.responses import FileResponse, Response

from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.impl.s3.s3_server_auth import S3ServerAuth
from gws_core.impl.s3.s3_server_fastapi_app import s3_server_app
from gws_core.impl.s3.s3_server_service import S3ServerService


@s3_server_app.get("/health-check")
async def health_check() -> bool:
    return True


@s3_server_app.put("/v1/{bucket}/{key:path}")
async def upload_object(request: Request,
                        bucket: str, key: str,
                        _=Depends(S3ServerAuth.check_s3_server_auth)):

    if not key:
        S3ServerService.create_bucket(bucket)
    else:
        file_bytes = await request.body()
        S3ServerService.upload_object(bucket, key, file_bytes)
    return ResponseHelper.create_xml_response('')


@s3_server_app.get("/v1/{bucket}/{key:path}")
def download_object(bucket: str, key: str,
                    _=Depends(S3ServerAuth.check_s3_server_auth)) -> FileResponse:
    return S3ServerService.get_object(bucket, key)


@s3_server_app.get("/v1/{bucket}")
def list_objects(bucket: str,
                 max_keys: int = Query(1000, alias='max-keys'),
                 prefix: str = Query(None, alias='prefix'),
                 _=Depends(S3ServerAuth.check_s3_server_auth)):
    result = S3ServerService.list_objects(bucket,
                                          prefix=prefix, max_keys=max_keys)

    return ResponseHelper.create_xml_response_from_json({'ListBucketResult': result})


@s3_server_app.head("/v1/{bucket}/{key:path}")
def head_object(bucket: str, key: str,
                _=Depends(S3ServerAuth.check_s3_server_auth)):
    S3ServerService.head_object(bucket, key)


@s3_server_app.delete("/v1/{bucket}/{key:path}")
def delete_object(bucket: str, key: str,
                  _=Depends(S3ServerAuth.check_s3_server_auth)):

    S3ServerService.delete_object(bucket, key)

    return Response(status_code=204)
