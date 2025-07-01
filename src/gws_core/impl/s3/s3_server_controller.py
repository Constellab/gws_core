

from typing import List, Union

from fastapi import Depends, Request
from fastapi.params import Query
from fastapi.responses import Response

from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.core.utils.xml_helper import XMLHelper
from gws_core.impl.s3.abstract_s3_service import AbstractS3Service
from gws_core.impl.s3.s3_server_auth import S3ServerAuth
from gws_core.impl.s3.s3_server_fastapi_app import s3_server_app

TAG_HEADER = 'x-amz-tagging'


# Controller that act like a simple s3 server. To develop a new route
# trigger the s3 request from the client and check the request structure in
# s3_server_fastapi_app.all_http_exception_handler HTTP handler.
# Also use doc : https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations.html


@s3_server_app.get("/health-check")
def health_check() -> bool:
    return True


@s3_server_app.get("v1/health-check")
def health_check_v1() -> bool:
    return True


# Route call for multiple command. The x_id content the command.
# the trailing slash is important to make the route work
@s3_server_app.post("/v1/{bucket}/")
async def post(request: Request,
               delete: str = Query(None, alias='delete'),
               x_id: str = Query(None, alias='x-id'),
               service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth)) -> Response:
    if x_id == 'DeleteObjects' or delete == '':
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
        service.delete_objects(keys)
        return Response(status_code=204)

    else:
        raise Exception('Not implemented')


@s3_server_app.put("/v1/{bucket}")
def create_bucket(service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth)) -> Response:
    service.create_bucket()
    return ResponseHelper.create_xml_response('')


# use async to await the body of the request
@s3_server_app.put("/v1/{bucket}/{key:path}")
async def upload_object(
        key: str,
        request: Request,
        tagging: str = Query(None, alias='tagging'),
        service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth)) -> Response:
    # update tags
    if key and tagging == '':
        file_bytes = await request.body()
        body = XMLHelper.xml_to_dict(file_bytes.decode('utf-8'))
        service.update_object_tags(key, body.get('Tagging', {}))
        return ResponseHelper.create_xml_response('')
    # upload object
    if key:
        file_bytes = await request.body()
        tags = service.convert_query_param_string_to_dict(request.headers.get(TAG_HEADER))
        service.upload_object(key, file_bytes, tags)
        return ResponseHelper.create_xml_response('')
    else:
        service.create_bucket()
        return ResponseHelper.create_xml_response('')


@s3_server_app.get("/v1/{bucket}/{key:path}")
def download_object(key: str,
                    tagging: str = Query(None, alias='tagging'),
                    max_keys: int = Query(1000, alias='max-keys'),
                    prefix: str = Query(None, alias='prefix'),
                    delimiter: str = Query(None, alias='delimiter'),
                    service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth)) -> Response:
    if key and tagging == '':
        tags = service.get_object_tags(key)
        return ResponseHelper.create_xml_response_from_json({'Tagging': tags})
    if not key:
        result = service.list_objects(prefix=prefix, max_keys=max_keys, delimiter=delimiter)
        return ResponseHelper.create_xml_response_from_json({'Tagging': result})
    return service.get_object(key)


@s3_server_app.get("/v1/{bucket}")
def list_objects(max_keys: int = Query(1000, alias='max-keys'),
                 prefix: str = Query(None, alias='prefix'),
                 delimiter: str = Query(None, alias='delimiter'),
                 continuation_token: str = Query(None, alias='continuation-token'),
                 marker: str = Query(None, alias='marker'),  # support for old API
                 start_after: str = Query(None, alias='start-after'),
                 service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth)) -> Response:
    result = service.list_objects(prefix=prefix, max_keys=max_keys, delimiter=delimiter,
                                  continuation_token=continuation_token or marker, start_after=start_after)

    return ResponseHelper.create_xml_response_from_json({'ListBucketResult': result})


@s3_server_app.head("/v1/{bucket}/{key:path}")
def head_object(key: str,
                service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth)) -> Response:
    headers = service.head_object(key)

    return Response(status_code=200, headers=headers)


@s3_server_app.delete("/v1/{bucket}/{key:path}")
def delete_object(key: str,
                  service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth)) -> Response:
    service.delete_object(key)

    return Response(status_code=204)
