import docker

import docker.types
import grpc
from proto import scaler_pb2 as pb_msgs
from proto import scaler_pb2_grpc as pb
from google.protobuf.empty_pb2 import Empty

from loguru import logger
import pytest
import os


GRPC_SERVER_ADDR = os.environ.get("GRPC_SERVER_ADDR")
scaler_stub: pb.ScalerStub
docker_client: docker.DockerClient


@pytest.fixture(scope="session", autouse=True)
def init():
    global scaler_stub
    global docker_client

    docker_client = docker.from_env()
    channel = grpc.insecure_channel(GRPC_SERVER_ADDR)
    scaler_stub = pb.ScalerStub(channel=channel)


def test_local():
    global scaler_stub
    resp: pb_msgs.ListNodesResponse = scaler_stub.ListNodes(Empty())
    logger.info(resp.nodes)
    assert len(resp.nodes) == 0

    new_node: pb_msgs.CreateNodeResponse = scaler_stub.CreateNode(
        pb_msgs.CreateNodeRequest(platform="local", backend="localhost:8080"))
    logger.info(f"New node id: {new_node.node_id}")
    container = docker_client.containers.get(new_node.node_id)
    assert container.short_id == new_node.node_id
    assert container.status == "running"

    resp: pb_msgs.ListNodesResponse = scaler_stub.ListNodes(Empty())
    assert len(resp.nodes) == 1
    assert resp.nodes[0].node_id == new_node.node_id
    assert resp.nodes[0].backend == "localhost:8080"
    assert resp.nodes[0].platform == "local"

    scaler_stub.DeleteNode(pb_msgs.DeleteNodeRequest(node_id=new_node.node_id))
    container = docker_client.containers.get(new_node.node_id)
    assert container.short_id == new_node.node_id
    assert container.status == "exited"
    assert len(scaler_stub.ListNodes(Empty()).nodes) == 0


# def test_vastai():
