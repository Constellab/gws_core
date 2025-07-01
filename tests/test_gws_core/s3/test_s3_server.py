

import os
from multiprocessing import Process
from time import sleep
from typing import List

import boto3
import requests
from mypy_boto3_s3.client import S3Client
from uvicorn import Config, Server

from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials import Credentials
from gws_core.credentials.credentials_service import CredentialsService
from gws_core.credentials.credentials_type import (CredentialsDataS3,
                                                   CredentialsDataS3LabServer,
                                                   CredentialsType,
                                                   SaveCredentialsDTO)
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.s3.datahub_s3_server_service import DataHubS3ServerService
from gws_core.impl.s3.s3_server_fastapi_app import s3_server_app
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.test.base_test_case import BaseTestCase


# test_s3_server.py
class TestS3Server(BaseTestCase):

    DATAHUB_ACCESS_KEY_ID = 'access_key'
    DATAHUB_SECRET_KEY = 'secret_key'

    BASIC_BUCKET_NAME = 'test-bucket'
    BASIC_ACCESS_KEY_ID = 'basic_access_key'
    BASIC_SECRET_KEY = 'basic_secret_key'

    CURRENT_FILE_ABSPATH = os.path.abspath(__file__)
    CURRENT_FILE_NAME = os.path.basename(CURRENT_FILE_ABSPATH)

    def test_datahub_s3(self):
        folder: SpaceFolder = SpaceFolder(code='S3', title='S3').save()

        proc = self._start_s3_server()

        try:
            self._create_s3_credentials()

            # Test auth, access key and secret key are correct
            self._test_auth(self.DATAHUB_ACCESS_KEY_ID, self.DATAHUB_SECRET_KEY,
                            DataHubS3ServerService.FOLDERS_BUCKET_NAME)

            # Test CRUD
            self._test_datahub_s3(folder_id=folder.id)

        finally:
            # stop the server
            proc.terminate()  # send

    def test_lab_s3_server(self):
        proc = self._start_s3_server()

        tmp_dir = Settings.make_temp_dir()
        try:
            self._create_lab_s3_server_credentials(tmp_dir)

            # Test auth, access key and secret key are correct
            self._test_auth(self.BASIC_ACCESS_KEY_ID, self.BASIC_SECRET_KEY, self.BASIC_BUCKET_NAME)

            # Test CRUD
            self._test_basic_s3(tmp_dir)

        finally:
            # stop the server
            proc.terminate()  # send
            FileHelper.delete_dir(tmp_dir)

    def _test_auth(self, access_key: str, secret_key: str, bucket_name: str):
        s3_client = self._create_client(access_key_id=access_key, secret_key=secret_key)
        s3_client.create_bucket(Bucket=bucket_name)

        # test wrong access key
        s3_client = self._create_client(access_key_id='wrong_access_key', secret_key=secret_key)
        with self.assertRaises(Exception):
            s3_client.create_bucket(Bucket=bucket_name)

        # test wrong secret key
        s3_client = self._create_client(access_key_id=access_key, secret_key='wrong_secret_key')
        with self.assertRaises(Exception):
            s3_client.create_bucket(Bucket=bucket_name)

    def _test_datahub_s3(self, folder_id: str):
        s3_client = self._create_client(self.DATAHUB_ACCESS_KEY_ID, self.DATAHUB_SECRET_KEY)

        key = 'test.py'
        s3_client.upload_file(self.CURRENT_FILE_ABSPATH, Bucket=DataHubS3ServerService.FOLDERS_BUCKET_NAME, Key=key, ExtraArgs={
                              'Tagging': f"{DataHubS3ServerService.FOLDER_TAG_NAME}={folder_id}&{DataHubS3ServerService.NAME_TAG_NAME}=test.py"})

        # check resources
        resources: List[ResourceModel] = list(ResourceModel.select())
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].origin, ResourceOrigin.S3_FOLDER_STORAGE)
        self.assertEqual(resources[0].name, 'test.py')
        self.assertEqual(resources[0].folder.id, folder_id)

        # test list objects
        result = s3_client.list_objects_v2(Bucket=DataHubS3ServerService.FOLDERS_BUCKET_NAME)
        self.assertEqual(len(result['Contents']), 1)
        self.assertEqual(result['Contents'][0]['Key'], key)

        # test list with wrong prefix
        prefix = 'space-id/root-folder-id2/tt'
        result = s3_client.list_objects_v2(Bucket=DataHubS3ServerService.FOLDERS_BUCKET_NAME, Prefix=prefix)
        self.assertTrue('Contents' not in result)

        # test download file
        destination_folder = Settings.make_temp_dir()
        file_path = os.path.join(destination_folder, 'test.py')
        s3_client.download_file(Bucket=DataHubS3ServerService.FOLDERS_BUCKET_NAME, Key=key, Filename=file_path)
        self.assertTrue(FileHelper.exists_on_os(file_path))
        self.assertTrue(FileHelper.get_size(file_path) > 0)

        # test delete file
        s3_client.delete_object(Bucket=DataHubS3ServerService.FOLDERS_BUCKET_NAME, Key=key)

        # check resources
        resources = list(ResourceModel.select())
        self.assertEqual(len(resources), 0)

        # test list objects
        result = s3_client.list_objects_v2(Bucket=DataHubS3ServerService.FOLDERS_BUCKET_NAME)
        self.assertTrue('Contents' not in result)

    def _test_basic_s3(self, bucket_path: str):
        s3_client = self._create_client(
            access_key_id=self.BASIC_ACCESS_KEY_ID, secret_key=self.BASIC_SECRET_KEY)

        key = 'test.py'
        s3_client.upload_file(self.CURRENT_FILE_ABSPATH, Bucket=self.BASIC_BUCKET_NAME, Key=key)

        # check resources
        file_path_in_bucket = os.path.join(bucket_path, key)
        self.assertTrue(FileHelper.exists_on_os(file_path_in_bucket))

        # test list objects
        result = s3_client.list_objects_v2(Bucket=self.BASIC_BUCKET_NAME)
        self.assertEqual(len(result['Contents']), 1)
        self.assertEqual(result['Contents'][0]['Key'], key)

        # test list with wrong prefix
        prefix = 'space-id/root-folder-id2/tt'
        result = s3_client.list_objects_v2(Bucket=self.BASIC_BUCKET_NAME, Prefix=prefix)
        self.assertTrue('Contents' not in result)

        # test download file
        destination_folder = Settings.make_temp_dir()
        download_file_path = os.path.join(destination_folder, 'test.py')
        s3_client.download_file(Bucket=self.BASIC_BUCKET_NAME, Key=key, Filename=download_file_path)
        self.assertTrue(FileHelper.exists_on_os(download_file_path))
        self.assertTrue(FileHelper.get_size(download_file_path) > 0)

        # test pagination
        s3_client.upload_file(self.CURRENT_FILE_ABSPATH, Bucket=self.BASIC_BUCKET_NAME, Key='zzz.py')
        result = s3_client.list_objects_v2(Bucket=self.BASIC_BUCKET_NAME, MaxKeys=1)
        self.assertEqual(len(result['Contents']), 1)
        self.assertEqual(result['Contents'][0]['Key'], 'test.py')
        self.assertTrue('NextContinuationToken' in result)
        result = s3_client.list_objects_v2(Bucket=self.BASIC_BUCKET_NAME, MaxKeys=1,
                                           ContinuationToken=result['NextContinuationToken'])
        self.assertEqual(len(result['Contents']), 1)
        self.assertEqual(result['Contents'][0]['Key'], 'zzz.py')

        # test delete file
        s3_client.delete_object(Bucket=self.BASIC_BUCKET_NAME, Key=key)
        s3_client.delete_object(Bucket=self.BASIC_BUCKET_NAME, Key='zzz.py')
        self.assertFalse(FileHelper.exists_on_os(file_path_in_bucket))

        # test list objects
        result = s3_client.list_objects_v2(Bucket=self.BASIC_BUCKET_NAME)
        self.assertTrue('Contents' not in result)

    def _create_client(self, access_key_id: str, secret_key: str) -> S3Client:
        # test wrong secret key
        return boto3.client(
            's3',
            region_name='us-east-1',
            endpoint_url='http://localhost:3000/v1',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_key,
        )

        # test with local minio
        # return boto3.client(
        #     's3',
        #     region_name='us-east-1',
        #     endpoint_url='http://host.docker.internal:9000/',
        #     aws_access_key_id='dfoombSNxhD4iE1BqEUr',
        #     aws_secret_access_key='oXtEbbn8bpIj189wtOajc9NfFvzwbr6V386y6SAL',
        # )

    def _create_s3_credentials(self) -> Credentials:
        name = 'Test s3 server'

        credentials = CredentialsService.find_by_name(name)
        if credentials:
            return credentials
        s3_data = CredentialsDataS3(
            endpoint_url='test',
            bucket=DataHubS3ServerService.FOLDERS_BUCKET_NAME,
            region='us-east-1',
            access_key_id=self.DATAHUB_ACCESS_KEY_ID,
            secret_access_key=self.DATAHUB_SECRET_KEY
        )

        credentials_dto = SaveCredentialsDTO(name=name, type=CredentialsType.S3,
                                             description='Test s3 server', data=s3_data.to_json_dict())

        return CredentialsService.create(credentials_dto)

    def _create_lab_s3_server_credentials(
            self, bucket_path: str) -> Credentials:
        name = 'Test s3 lab server'

        credentials = CredentialsService.find_by_name(name)
        if credentials:
            return credentials
        s3_data = CredentialsDataS3LabServer(
            bucket=self.BASIC_BUCKET_NAME,
            bucket_local_path=bucket_path,
            access_key_id=self.BASIC_ACCESS_KEY_ID,
            secret_access_key=self.BASIC_SECRET_KEY
        )

        credentials_dto = SaveCredentialsDTO(name=name, type=CredentialsType.S3_LAB_SERVER,
                                             description='Test s3 server', data=s3_data.to_json_dict())

        return CredentialsService.create(credentials_dto)

    def _start_s3_server(self) -> Process:
        config = Config(app=s3_server_app, host="0.0.0.0", port=3000)
        server = Server(config)

        proc = Process(target=server.run)
        proc.start()

        count = 0

        #  wait for the api to be ready
        while True:
            print('Waiting for s3 server to be ready...')
            sleep(1)

            # make an http request to the server
            try:
                response = requests.get('http://localhost:3000/health-check', timeout=1000)
                if response.status_code == 200:
                    break
            except Exception as err:
                print(err)

            count += 1

            if count >= 15:
                proc.terminate()
                raise Exception('Timeout while starting s3 server')

        return proc
