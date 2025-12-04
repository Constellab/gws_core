from typing import List, Union

from fastapi import Depends, Request
from fastapi.params import Query
from fastapi.responses import Response

from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.core.utils.xml_helper import XMLHelper
from gws_core.impl.s3.abstract_s3_service import AbstractS3Service
from gws_core.impl.s3.s3_server_auth import S3ServerAuth
from gws_core.impl.s3.s3_server_fastapi_app import s3_server_app

TAG_HEADER = "x-amz-tagging"


# Controller that act like a simple s3 server. To develop a new route
# trigger the s3 request from the client and check the request structure in
# s3_server_fastapi_app.all_http_exception_handler HTTP handler.
# Also use doc : https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations.html
# Also possible to test with a local Minio server and postamn to see request structure.
# Start Minio : docker run -p 9000:9000 -p 9001:9001 minio/minio server /data --console-address ":9001"
# The connect with admin user/password (must be admin).
# Create a bucket and in the bucket options set the bucket public.
# The request should work. Upload a file and test the HEAD request: http://localhost:9000/{bucket}/{key}


@s3_server_app.get("/health-check")
def health_check() -> bool:
    return True


@s3_server_app.get("v1/health-check")
def health_check_v1() -> bool:
    return True


# Route call for multiple command. The x_id content the command.
# the trailing slash is important to make the route work
@s3_server_app.post("/v1/{bucket}/")
async def post(
    request: Request,
    delete: str = Query(None, alias="delete"),
    x_id: str = Query(None, alias="x-id"),
    service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth),
) -> Response:
    if x_id == "DeleteObjects" or delete == "":
        return await _delete_object(request, service)

    else:
        raise Exception("Not implemented")


async def _delete_object(request: Request, service: AbstractS3Service) -> Response:
    # Method to delete a single object
    xml_content = await request.body()
    str_xml = xml_content.decode("utf-8")
    dict_ = XMLHelper.xml_to_dict(str_xml)
    objects: Union[dict, List[dict]] = dict_["Delete"]["Object"]
    keys: list[str]
    if not isinstance(objects, list):
        keys = [objects["Key"]]
    else:
        keys = [obj["Key"] for obj in objects]
    service.delete_objects(keys)
    return Response(status_code=204)


@s3_server_app.put("/v1/{bucket}")
def create_bucket(
    service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth),
) -> Response:
    service.create_bucket()
    return ResponseHelper.create_xml_response("")


@s3_server_app.get("/v1/{bucket}/{key:path}")
def download_object(
    key: str,
    tagging: str = Query(None, alias="tagging"),
    max_keys: int = Query(1000, alias="max-keys"),
    prefix: str = Query(None, alias="prefix"),
    delimiter: str = Query(None, alias="delimiter"),
    service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth),
) -> Response:
    if key and tagging == "":
        tags = service.get_object_tags(key)
        return ResponseHelper.create_xml_response_from_json({"Tagging": tags})
    if not key:
        result = service.list_objects(prefix=prefix, max_keys=max_keys, delimiter=delimiter)
        return ResponseHelper.create_xml_response_from_json({"Tagging": result})
    return service.get_object(key)


@s3_server_app.get("/v1/{bucket}")
def list_objects(
    max_keys: int = Query(1000, alias="max-keys"),
    prefix: str = Query(None, alias="prefix"),
    delimiter: str = Query(None, alias="delimiter"),
    continuation_token: str = Query(None, alias="continuation-token"),
    marker: str = Query(None, alias="marker"),  # support for old API
    start_after: str = Query(None, alias="start-after"),
    service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth),
) -> Response:
    result = service.list_objects(
        prefix=prefix,
        max_keys=max_keys,
        delimiter=delimiter,
        continuation_token=continuation_token or marker,
        start_after=start_after,
    )

    return ResponseHelper.create_xml_response_from_json({"ListBucketResult": result})


@s3_server_app.head("/v1/{bucket}/{key:path}")
def head_object(
    key: str, service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth)
) -> Response:
    headers = service.head_object(key)

    return Response(status_code=200, headers=headers)


@s3_server_app.delete("/v1/{bucket}/{key:path}")
def delete_object(
    key: str, service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth)
) -> Response:
    service.delete_object(key)

    return Response(status_code=204)


# Multipart upload endpoints
@s3_server_app.post("/v1/{bucket}/{key:path}")
async def initiate_multipart_upload(
    key: str,
    request: Request,
    uploads: str = Query(None, alias="uploads"),
    upload_id: str = Query(None, alias="uploadId"),
    service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth),
) -> Response:
    if uploads == "":
        return _initiate_multipart_upload(key, request, service)

    elif upload_id:
        # Complete multipart upload
        return await _complete_multipart_upload(key, upload_id, request, service)
    else:
        return Response(status_code=400, content="Bad Request")


def _initiate_multipart_upload(key: str, request: Request, service: AbstractS3Service) -> Response:
    # Initiate a multipart upload
    mtime_timestamp = _extract_x_amz_meta_mtime(request)
    upload_id = service.initiate_multipart_upload(key, mtime_timestamp)

    return ResponseHelper.create_xml_response_from_json(
        {
            "InitiateMultipartUploadResult": {
                "Bucket": service.bucket_name,
                "Key": key,
                "UploadId": upload_id,
            }
        }
    )


async def _complete_multipart_upload(
    key: str, upload_id: str, request: Request, service: AbstractS3Service
) -> Response:
    # Complete a multipart upload
    xml_content = await request.body()
    str_xml = xml_content.decode("utf-8")
    dict_ = XMLHelper.xml_to_dict(str_xml)

    parts = dict_["CompleteMultipartUpload"]["Part"]
    if not isinstance(parts, list):
        parts = [parts]

    service.complete_multipart_upload(key, upload_id, parts)

    return ResponseHelper.create_xml_response_from_json(
        {
            "CompleteMultipartUploadResult": {
                "Location": f"http://localhost/{service.bucket_name}/{key}",
                "Bucket": service.bucket_name,
                "Key": key,
                "ETag": "",
            }
        }
    )


@s3_server_app.delete("/v1/{bucket}/{key:path}")
async def delete_multipart_upload_or_object(
    key: str,
    upload_id: str = Query(None, alias="uploadId"),
    service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth),
) -> Response:
    if upload_id:
        # Abort multipart upload
        service.abort_multipart_upload(key, upload_id)
        return Response(status_code=204)
    else:
        # Regular object deletion
        service.delete_object(key)
        return Response(status_code=204)


@s3_server_app.put("/v1/{bucket}/{key:path}")
async def upload_part_or_object(
    key: str,
    request: Request,
    tagging: str = Query(None, alias="tagging"),
    x_id: str = Query(None, alias="x-id"),
    part_number: int = Query(None, alias="partNumber"),
    upload_id: str = Query(None, alias="uploadId"),
    service: AbstractS3Service = Depends(S3ServerAuth.check_s3_server_auth),
) -> Response:
    if part_number and upload_id:
        return await _upload_part(request, key, upload_id, part_number, service)

    # Regular object upload (existing functionality)
    if x_id == "CopyObject":
        raise NotImplementedError("CopyObject operation is not implemented in this S3 server.")
    # update tags
    if key and tagging == "":
        return await _update_object_tags(request, key, service)
    # upload object
    if key:
        return await _upload_object(request, key, service)
    else:
        service.create_bucket()
        return ResponseHelper.create_xml_response("")


async def _upload_part(
    request: Request, key: str, upload_id: str, part_number: int, service: AbstractS3Service
) -> Response:
    # Upload part for multipart upload
    file_bytes = await request.body()
    service.upload_part(key, upload_id, part_number, file_bytes)
    return Response(status_code=200, headers={"ETag": f""})


async def _update_object_tags(request: Request, key: str, service: AbstractS3Service) -> Response:
    # Update tags for an object
    file_bytes = await request.body()
    body = XMLHelper.xml_to_dict(file_bytes.decode("utf-8"))
    service.update_object_tags(key, body.get("Tagging", {}))
    return ResponseHelper.create_xml_response("")


async def _upload_object(request: Request, key: str, service: AbstractS3Service) -> Response:
    # Upload an object to the bucket
    file_bytes = await request.body()
    tags = service.convert_query_param_string_to_dict(request.headers.get(TAG_HEADER))

    # Extract modification time from headers (rclone sends this)
    mtime_timestamp = _extract_x_amz_meta_mtime(request)
    response_headers = service.upload_object(key, file_bytes, tags, last_modified=mtime_timestamp)

    return Response(status_code=200, headers=response_headers)


def _extract_x_amz_meta_mtime(request: Request) -> float:
    """Extract x-amz-meta-mtime header as a float."""
    mtime_header = request.headers.get("x-amz-meta-mtime")
    if mtime_header:
        try:
            return float(mtime_header)
        except (ValueError, TypeError):
            pass
    return None
