# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from multiprocessing import Process
from time import sleep

import boto3
import requests
from mypy_boto3_s3.client import S3Client
from uvicorn import Config, Server

from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials import Credentials
from gws_core.credentials.credentials_dto import SaveCredentialDTO
from gws_core.credentials.credentials_service import CredentialsService
from gws_core.credentials.credentials_type import (CredentialsDataS3,
                                                   CredentialsType)
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.s3.s3_server_fastapi_app import s3_server_app
from gws_core.test.base_test_case import BaseTestCase


# test_s3_server.py
class TestS3Server(BaseTestCase):

    access_key_id = 'access_key'
    secret_access_key = 'secret_key'

    current_file_abspath = os.path.abspath(__file__)

    def test_s3(self):

        proc = self._start_s3_server()

        try:
            self._create_credentials()

            # Test auth, access key and secret key are correct
            self._test_auth()

            # Test upload file
            self._test_operations()
        finally:
            # stop the server
            proc.terminate()  # send

    def _test_auth(self):
        s3_client = self._create_client()
        s3_client.list_objects_v2(Bucket='project')

        # test wrong access key
        s3_client = self._create_client(access_key_id='wrong_access_key')
        with self.assertRaises(Exception):
            s3_client.list_objects_v2(Bucket='project')

        # test wrong secret key
        s3_client = self._create_client(secret_key='wrong_secret_key')
        with self.assertRaises(Exception):
            s3_client.list_objects_v2(Bucket='project')

    def _test_operations(self):
        s3_client = self._create_client()
        s3_client.upload_file(self.current_file_abspath, Bucket='super', Key='test.py')

        # test list objects
        result = s3_client.list_objects_v2(Bucket='super')
        self.assertEqual(len(result['Contents']), 1)
        key = result['Contents'][0]['Key']

        # test download file
        destination_folder = Settings.make_temp_dir()
        file_path = os.path.join(destination_folder, 'test.py')
        s3_client.download_file(Bucket='super', Key=key, Filename=file_path)
        self.assertTrue(FileHelper.exists_on_os(file_path))
        self.assertTrue(FileHelper.get_size(file_path) > 0)

        # test delete file
        s3_client.delete_object(Bucket='super', Key=key)

        # test list objects
        result = s3_client.list_objects_v2(Bucket='super')
        self.assertTrue('Contents' not in result)

    def _create_client(self, access_key_id: str = None, secret_key: str = None) -> S3Client:
        # test wrong secret key
        return boto3.client(
            's3',
            region_name='us-east-1',
            endpoint_url='http://localhost:3000/v1',
            aws_access_key_id=access_key_id or self.access_key_id,
            aws_secret_access_key=secret_key or self.secret_access_key,
        )

    def _create_credentials(self) -> Credentials:
        name = 'Test s3 server'

        credentials = CredentialsService.find_by_name(name)
        if credentials:
            return credentials
        s3_data: CredentialsDataS3 = {
            'endpoint_url': 'test',
            'bucket': '',
            'region': 'us-east-1',
            'access_key_id': 'access_key',
            'secret_access_key': 'secret_key'
        }

        credentials_dto = SaveCredentialDTO(name='Test s3 server', type=CredentialsType.S3,
                                            description='Test s3 server', data=s3_data)

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
                response = requests.get('http://localhost:3000/v1/health-check')
                if response.status_code == 200:
                    break
            except Exception as err:
                print(err)

            count += 1

            if count >= 15:
                proc.terminate()
                raise Exception('Timeout while starting s3 server')

        return proc
