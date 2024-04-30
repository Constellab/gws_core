import biolectorxtremotecontrol_pb2_grpc as biolector
import grpc
from google.protobuf import empty_pb2, wrappers_pb2

with grpc.insecure_channel('host.docker.internal:50051') as channel:
    # print(channel)
    service = biolector.BioLectorXtRemoteControlStub(channel)
    print('Protocol', service.GetProtocols(empty_pb2.Empty(), timeout=10))

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
