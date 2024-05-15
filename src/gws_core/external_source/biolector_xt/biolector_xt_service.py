
import os
from typing import Generator, List

import grpc
from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import BoolValue, StringValue

from gws_core.core.utils.settings import Settings
from gws_core.external_source.biolector_xt.biolector_xt_dto import \
    CredentialsDataBiolector
from gws_core.external_source.biolector_xt.grpc.biolectorxtremotecontrol_pb2 import (
    ContinueProtocolResponse, FileChunk, GetExperimentListResponse, MetaData,
    ProtocolInfo, StartProtocolResponse, StatusUpdateStreamResponse,
    StdResponse, StopProtocolResponse)
from gws_core.external_source.biolector_xt.grpc.biolectorxtremotecontrol_pb2_grpc import \
    BioLectorXtRemoteControlStub
from gws_core.impl.file.file_helper import FileHelper


class BiolectorXTService():
    """Service to interact with the Biolector XT device using gRPC
    """

    _credentials: CredentialsDataBiolector

    timeout = 10

    def __init__(self, credentials: CredentialsDataBiolector) -> None:
        self._credentials = credentials

    def get_protocols(self) -> List[ProtocolInfo]:
        with self.get_grpc_channed() as channel:
            stub = BioLectorXtRemoteControlStub(channel)
            return stub.GetProtocols(Empty(), timeout=self.timeout)

    def get_experiments(self) -> GetExperimentListResponse:
        with self.get_grpc_channed() as channel:
            stub = BioLectorXtRemoteControlStub(channel)
            return stub.GetExperimentList(Empty(), timeout=self.timeout)

    def upload_protocol(self, file_path: str) -> StdResponse:
        if not FileHelper.exists_on_os(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with self.get_grpc_channed() as channel:
            stub = BioLectorXtRemoteControlStub(channel)

            return stub.UploadProtocol(self._upload_protocol_chunker(file_path), timeout=self.timeout)

    def _upload_protocol_chunker(self, file_path: str) -> Generator:
        """
        helper function to chop up a local file to smaller chunks that can be send via gRPC
        """
        meta_data = MetaData(filename=file_path)
        chunk_size = 50000  # maximum chunk size 131071
        chunk_list = []
        byte_array = []
        with open(file_path, "rb") as binary_file:
            byte = binary_file.read(chunk_size)
            while byte:
                byte_array.append(byte)
                byte = binary_file.read(chunk_size)

            # Send the file name first
            file_chunk = FileChunk(
                metadata=meta_data
            )
            yield file_chunk

            for chunk in byte_array:
                # send the data chunks
                file_chunk = FileChunk(
                    chunk_data=chunk
                )
                chunk_list.append(file_chunk)
                yield file_chunk

    def start_protocol(self, protocol_id: str) -> StartProtocolResponse:
        with self.get_grpc_channed() as channel:
            stub = BioLectorXtRemoteControlStub(channel)
            return stub.StartProtocol(StringValue(value=protocol_id), timeout=self.timeout)

    def stop_current_protocol(self) -> StopProtocolResponse:
        with self.get_grpc_channed() as channel:
            stub = BioLectorXtRemoteControlStub(channel)
            return stub.StopProtocol(Empty(), timeout=self.timeout)

    def pause_current_protocol(self) -> None:
        with self.get_grpc_channed() as channel:
            stub = BioLectorXtRemoteControlStub(channel)
            return stub.PauseProtocol(BoolValue(value=True), timeout=self.timeout)

    def resume_current_protocol(self) -> ContinueProtocolResponse:
        with self.get_grpc_channed() as channel:
            stub = BioLectorXtRemoteControlStub(channel)
            return stub.ContinueProtocol(Empty(), timeout=self.timeout)

    def download_experiment(self, experiment_id: str) -> str:
        """Download the experiment as a zip file and return the path to the file

        :param experiment_id: id of the experiment to download
        :type experiment_id: str
        :return: path to the downloaded file
        :rtype: str
        """
        with self.get_grpc_channed() as channel:
            stub = BioLectorXtRemoteControlStub(channel)
            chunk: FileChunk = stub.DownloadExperiment(StringValue(value=experiment_id), timeout=self.timeout)

            tmp_dir = Settings.make_temp_dir()
            file_path = os.path.join(tmp_dir, f"{experiment_id}.zip")

            with open(file_path, "wb") as file:
                file.write(chunk.chunk_data)

            return file_path

    def get_status_update_stream(self) -> StatusUpdateStreamResponse:
        with self.get_grpc_channed() as channel:
            stub = BioLectorXtRemoteControlStub(channel)
            return stub.StatusUpdateStream(Empty(), timeout=self.timeout)

    def get_grpc_channed(self) -> grpc.Channel:
        if self._credentials.secure_channel:
            # TODO DEFINE CREDENTIALS
            return grpc.secure_channel(self._credentials.endpoint_url, credentials=None)
        else:
            return grpc.insecure_channel(self._credentials.endpoint_url)
