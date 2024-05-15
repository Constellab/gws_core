import biolectorxtremotecontrol_pb2
import biolectorxtremotecontrol_pb2_grpc
import grpc

channel = grpc.insecure_channel('localhost:50051')


def Chunker(local_file_path):
    """
    helper function to chop up a local file to smaller chunks that can be send via gRPC
    """
    meta_data = biolectorxtremotecontrol_pb2.MetaData(filename=local_file_path)
    chunk_size = 50000  # maximum chunk size 131071
    Chunk_list = []
    byte_array = []
    with open(local_file_path, "rb") as binary_file:
        byte = binary_file.read(chunk_size)
        while byte:
            byte_array.append(byte)
            byte = binary_file.read(chunk_size)

        byte_counter_down = len(byte_array)
        byte_counter_up = 0

        # Send the file name first
        file_Chunk = biolectorxtremotecontrol_pb2.FileChunk(
            metadata=meta_data
        )
        yield file_Chunk

        for Chunk in byte_array:
            # send the data chunks
            file_Chunk = biolectorxtremotecontrol_pb2.FileChunk(
                chunk_data=Chunk
            )
            Chunk_list.append(file_Chunk)
            yield file_Chunk
            byte_counter_up += chunk_size
            byte_counter_down -= chunk_size


def upload_protocol(filename):
    """
    Uploads the protocol with the given filename.
    """
    stub = biolectorxtremotecontrol_pb2_grpc.BioLectorXtRemoteControlStub(channel)

    response = biolectorxtremotecontrol_pb2.StdResponse()
    try:
        response = stub.UploadProtocol(Chunker(filename))
    except grpc.RpcError as rpc_error:
        print(f"Error in upload_protocol: {rpc_error}")

    return response


# upload protocol
upload_protocol("/lab/user/bricks/gws_core/src/gws_core/external_source/python/protocol.json")
