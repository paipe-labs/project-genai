import scaler
from logger import logger

import grpc
import proto.scaler_pb2 as pb_msgs
import proto.scaler_pb2_grpc as pb
import google.protobuf.empty_pb2

import os
import typing
from concurrent import futures

SERVER_ADDR = os.environ.get("GRPC_SERVER_ADDR", "0.0.0.0:51075")


class Scaler(pb.ScalerServicer):
    def CreateNode(self, request: pb_msgs.CreateNodeRequest, context) -> pb_msgs.CreateNodeResponse:
        try:
            node_id = scaler.create_node(platform=request.platform,
                                         backend=request.backend,
                                         prov_script=request.prov_script,
                                         image=request.image,
                                         vastai_iid=request.vastai_iid)
            return pb_msgs.CreateNodeResponse(node_id=node_id)
        except Exception as e:
            logger.error(e)
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_details(e)
            return pb_msgs.CreateNodeResponse()

    def DeleteNode(self, request: pb_msgs.DeleteNodeRequest, context) -> pb_msgs.DeleteNodeResponse:
        try:
            scaler.delete_node(node_id=request.node_id)
        except Exception as e:
            logger.error(e)
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_details(e)
        return pb_msgs.DeleteNodeResponse()

    def ListNodes(self, _: google.protobuf.empty_pb2.Empty, context) -> pb_msgs.ListNodesResponse:
        try:
            node_info = [pb_msgs.NodeInfo(node_id=id, platform=info.platform,
                                          backend=info.backend, image=info.image) for id, info in scaler.list.nodes]
            return pb_msgs.ListNodesResponse(nodes=node_info)
        except Exception as e:
            logger.error(e)
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_details(e)
            return pb_msgs.ListNodesResponse()


if __name__ == "__main__":
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb.add_ScalerServicer_to_server(Scaler(), server)
    server.add_insecure_port(SERVER_ADDR)
    server.start()
    logger.info("gRPC Scaler server started")
    server.wait_for_termination()
