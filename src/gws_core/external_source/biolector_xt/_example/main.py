from json import dumps, loads

import biolectorxtremotecontrol_pb2_grpc as biolector
import grpc
from biolectorxtremotecontrol_pb2 import FileChunk, MetaData
from google.protobuf import empty_pb2, wrappers_pb2


def read_in_chunks(file_path, chunk_size=1024):
    with open(file_path, 'rb') as file:
        while True:
            chunk_data = file.read(chunk_size)
            if not chunk_data:
                break
            yield chunk_data


def request_iterator(file_path, filename):
    # Create a MetaData object
    metadata = MetaData(filename=filename)
    # file_chunk = FileChunk(metadata=metadata)
    # yield file_chunk

    # # Create a FileChunk object for each chunk
    for chunk_data in read_in_chunks(file_path):
        # file_chunk = FileChunk(metadata=metadata, chunk_data=chunk_data)
        file_chunk = FileChunk(chunk_data=chunk_data)
        yield file_chunk


with grpc.insecure_channel('host.docker.internal:50051') as channel:
    # print(channel)
    service = biolector.BioLectorXtRemoteControlStub(channel)
    print('Protocol', service.GetProtocols(empty_pb2.Empty(), timeout=10))

    # file_path = '/lab/user/bricks/gws_core/src/gws_core/external_source/python/26_2 24 81 BXT.json'
    # # read file as string and upload
    # # with open(file_path, 'r') as file:
    # #     file_content = file.read()
    # #     print('Protocol 1', service.UploadProtocol(wrappers_pb2.StringValue(value=file_content), timeout=10))

    # # read file as string and upload
    # with open(file_path, 'r') as file:
    #     file_content = file.read()
    #     # Create an iterator that yields the file content in chunks

    #     json_content = {
    #         "chunk_data": loads(file_content),
    #         "metadata": {
    #             "filename": "26_2 24 81 BXT.json",
    #         }
    #     }

    #     str_json = dumps(json_content)

    #     def request_iterator():
    #         for chunk in str_json:
    #             yield wrappers_pb2.StringValue(value=chunk)
    #     print('Protocol 1', service.UploadProtocol(request_iterator(), timeout=10))

    # Use the iterator when calling the UploadProtocol method
    file_path = '/lab/user/bricks/gws_core/src/gws_core/external_source/python/26_2 24 81 BXT.json'
    filename = '26_2 24 81 BXT.json'
    metadata = [
        ("initial-metadata-1", "The value should be str"),
        ("accesstoken", "gRPC Python is great"),
    ]
    response = service.UploadProtocol(request_iterator(file_path, filename), timeout=10,
                                      metadata=metadata)

    print('Protocol 2', service.GetProtocols(empty_pb2.Empty(), timeout=10))
    # # Historical data
    # experimental_list = service.GetExperimentList(empty_pb2.Empty(), timeout=10)
    # print(experimental_list)

    # # # Turn to json / python dict...
    # # print(experimental_list)
    # obj = wrappers_pb2.StringValue(value="{a7f03c66-3106-4f57-99c4-f652835a9fc5}")

    # # Live data
    # experiment = service.DownloadExperiment(obj)
    # output = open("biolector.zip", "wb")

    # while (True):
    #     try:
    #         fileChunk = experiment.next().chunk_data
    #         print(fileChunk)
    #         output.write(fileChunk)
    #     except StopIteration:
    #         # End of the filestream
    #         output.close()
    #         break
