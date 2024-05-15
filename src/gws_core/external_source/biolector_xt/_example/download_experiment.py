import biolectorxtremotecontrol_pb2
import biolectorxtremotecontrol_pb2_grpc
import grpc
from google.protobuf.wrappers_pb2 import StringValue

channel = grpc.insecure_channel('localhost:50051')


def download_experiment(id):
    """
    Downloads the experiment with the given id.
    """
    stub = biolectorxtremotecontrol_pb2_grpc.BioLectorXtRemoteControlStub(channel)

    response = biolectorxtremotecontrol_pb2.StdResponse()
    try:
        response = stub.DownloadExperiment(StringValue(value=id))
    except grpc.RpcError as rpc_error:
        print(f"Error in download_experiment: {rpc_error}")

    return response
