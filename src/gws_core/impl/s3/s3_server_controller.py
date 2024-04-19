

from typing import List, Union

from fastapi import Depends, Request
from fastapi.params import Query
from fastapi.responses import FileResponse, Response

from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.core.utils.xml_helper import XMLHelper
from gws_core.impl.s3.s3_server_auth import S3ServerAuth
from gws_core.impl.s3.s3_server_fastapi_app import s3_server_app
from gws_core.impl.s3.s3_server_service import S3ServerService

# Controller that act like a simple s3 server. To develop a new route
# trigger the s3 request from the client and check the request structure in
# s3_server_fastapi_app.all_http_exception_handler HTTP handler.


@s3_server_app.get("/health-check")
def health_check() -> bool:
    return True


# Route call for multiple command. The x_id content the command.
# the trailing slash is important to make the route work
@s3_server_app.post("/v1/{bucket}/")
async def post(bucket: str,
               request: Request,
               x_id: str = Query(None, alias='x-id'),
               _=Depends(S3ServerAuth.check_s3_server_auth)) -> Response:

    if x_id == 'DeleteObjects':
        # Method to delete multiple objects
        # return await delete_objectjj(bucket, request)
        xml_content = await request.body()
        str_xml = xml_content.decode('utf-8')
        dict_ = XMLHelper.xml_to_dict(str_xml)
        objects: Union[dict, List[dict]] = dict_['Delete']['Object']
        keys: list[str]
        if not isinstance(objects, list):
            keys = [objects['Key']]
        else:
            keys = [obj['Key'] for obj in objects]
        S3ServerService.delete_objects(bucket, keys)
        return Response(status_code=204)

    else:
        raise Exception('Not implemented')


@s3_server_app.put("/v1/{bucket}")
def create_bucket(bucket: str,
                  _=Depends(S3ServerAuth.check_s3_server_auth)) -> Response:

    S3ServerService.create_bucket(bucket)

    return ResponseHelper.create_xml_response('')


# use async to await the body of the request
@s3_server_app.put("/v1/{bucket}/{key:path}")
async def upload_object(
        bucket: str, key: str,
        request: Request,
        _=Depends(S3ServerAuth.check_s3_server_auth)) -> Response:

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
                 _=Depends(S3ServerAuth.check_s3_server_auth)) -> Response:
    result = S3ServerService.list_objects(bucket,
                                          prefix=prefix, max_keys=max_keys)

    return ResponseHelper.create_xml_response_from_json({'ListBucketResult': result})


@s3_server_app.head("/v1/{bucket}/{key:path}")
def head_object(bucket: str, key: str,
                _=Depends(S3ServerAuth.check_s3_server_auth)) -> Response:
    headers = S3ServerService.head_object(bucket, key)

    return Response(status_code=200, headers=headers)


@s3_server_app.delete("/v1/{bucket}/{key:path}")
def delete_object(bucket: str, key: str,
                  _=Depends(S3ServerAuth.check_s3_server_auth)) -> Response:

    S3ServerService.delete_object(bucket, key)

    return Response(status_code=204)
